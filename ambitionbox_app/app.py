"""AmbitionBox company analysis - Flask app."""

import io
import os
import re
import math

import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify, Response

try:
    from .history_routes import register_history_routes
    from .config import AppConfig
    from .cache import TTLCache, make_cache_key
    from .data_runtime import DatasetRuntime
except ImportError:  # pragma: no cover
    from history_routes import register_history_routes
    from config import AppConfig
    from cache import TTLCache, make_cache_key
    from data_runtime import DatasetRuntime

app = Flask(__name__)
app.config["SECRET_KEY"] = AppConfig.SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = AppConfig.DATA_PATH or os.path.join(BASE_DIR, "data", "companies.csv")

COLUMNS = ["company_name", "company_rating", "industry", "size",
           "type", "years_old", "location"]

# Short-lived bounded caches keep repeated dashboard/table requests from
# repeatedly executing expensive pandas operations. The CSV modification time
# is part of each cache key, so a refresh naturally invalidates old entries.
API_CACHE = TTLCache(maxsize=128, ttl_seconds=30)


def load_data(path: str | os.PathLike[str]) -> pd.DataFrame:
    df = pd.read_csv(path)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    df["company_name"] = df["company_name"].astype("string")
    df["company_rating"] = pd.to_numeric(df["company_rating"], errors="coerce")
    df["years_old"] = pd.to_numeric(df["years_old"], errors="coerce")
    for c in ["industry", "size", "type", "location"]:
        df[c] = df[c].astype("string")
    return df[COLUMNS].copy()


def data_version() -> str:
    """Return a cheap version token that changes when the dataset is rewritten."""
    try:
        stat = os.stat(DATA_PATH)
        return f"{stat.st_mtime_ns}:{stat.st_size}"
    except OSError:
        return "missing"


DATA_RUNTIME = DatasetRuntime(DATA_PATH, load_data, API_CACHE)
DF = DATA_RUNTIME.get()


def size_lower_bound(label):
    if not isinstance(label, str):
        return math.inf
    t = label.replace("(Global)", "").strip()
    m = re.match(r"([\d.]+)\s*(k|Lakh)?", t, flags=re.IGNORECASE)
    if not m:
        return math.inf
    num = float(m.group(1))
    unit = (m.group(2) or "").lower()
    if unit == "k":
        num *= 1_000
    elif unit == "lakh":
        num *= 100_000
    return num


def ordered_sizes(df):
    sizes = [s for s in df["size"].dropna().unique().tolist()]
    sizes.sort(key=lambda s: (size_lower_bound(s), "(Global)" in s))
    return sizes


def build_meta(df: pd.DataFrame) -> dict:
    return {
        "totals": {
            "companies": int(len(df)),
            "rated": int(df["company_rating"].notna().sum()),
            "industries": int(df["industry"].nunique()),
            "locations": int(df["location"].nunique()),
            "types": int(df["type"].nunique()),
            "avg_rating": round(float(df["company_rating"].mean()), 2),
            "avg_years": round(float(df["years_old"].mean()), 1),
            "oldest": int(df["years_old"].max()),
        },
        "filters": {
            "industries": sorted(df["industry"].dropna().unique().tolist()),
            "sizes": ordered_sizes(df),
            "types": sorted(df["type"].dropna().unique().tolist()),
            "locations": sorted(df["location"].dropna().unique().tolist()),
            "rating": {"min": 1.0, "max": 5.0},
            "years": {
                "min": int(df["years_old"].min()),
                "max": int(df["years_old"].max()),
            },
        },
    }


META = build_meta(DF)


def refresh_runtime() -> bool:
    """Reload the dataset when its file fingerprint changes.

    Returns True when a new DataFrame was loaded. A failed reload leaves the
    previous known-good DataFrame in place and is allowed to raise so the
    request surfaces the actual read/validation error.
    """
    global DF, META
    before = DATA_RUNTIME.version
    fresh = DATA_RUNTIME.get()
    if DATA_RUNTIME.version != before:
        DF = fresh
        META = build_meta(DF)
        return True
    return False


@app.before_request
def _refresh_dataset_before_request():
    refresh_runtime()


def _floats(name):
    v = request.args.get(name, None)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    q = df
    name = request.args.get("company_name", "").strip()
    if name:
        q = q[q["company_name"].str.contains(re.escape(name), case=False, na=False)]
    for field in ["industry", "size", "type", "location"]:
        vals = request.args.getlist(field)
        if vals:
            q = q[q[field].isin(vals)]
    rmin, rmax = _floats("rating_min"), _floats("rating_max")
    if rmin is not None:
        q = q[q["company_rating"] >= rmin]
    if rmax is not None:
        q = q[q["company_rating"] <= rmax]
    ymin, ymax = _floats("years_min"), _floats("years_max")
    include_unknown = request.args.get("include_unknown_age", "true") != "false"
    if ymin is not None or ymax is not None or not include_unknown:
        cond = pd.Series(True, index=q.index)
        if ymin is not None:
            cond &= q["years_old"] >= ymin
        if ymax is not None:
            cond &= q["years_old"] <= ymax
        if include_unknown:
            cond |= q["years_old"].isna()
        else:
            cond &= q["years_old"].notna()
        q = q[cond]
    return q


@app.route("/")
def index():
    return render_template("index.html", totals=META["totals"])


@app.route("/explore")
def explore():
    return render_template("explore.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/about")
def about():
    return render_template("about.html", totals=META["totals"])


@app.route("/compare")
def compare():
    return render_template("compare.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "ambitionbox-analysis", "data_records": int(len(DF))})


@app.route("/api/meta")
def api_meta():
    return jsonify(META)


@app.route("/api/companies")
def api_companies():
    query = request.query_string.decode("utf-8")
    key = make_cache_key("companies", f"{data_version()}:{query}")
    cached = API_CACHE.get(key)
    if cached is not None:
        return jsonify(cached)

    q = apply_filters(DF)
    sort = request.args.get("sort", "company_rating")
    order = request.args.get("order", "desc")
    if sort not in COLUMNS:
        sort = "company_rating"
    q = q.sort_values(by=sort, ascending=(order == "asc"), na_position="last", kind="mergesort")
    total = int(len(q))
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(200, max(5, int(request.args.get("page_size", 25))))
    except ValueError:
        page, page_size = 1, 25
    start = (page - 1) * page_size
    rows = q.iloc[start:start + page_size].copy().replace({np.nan: None})
    records = rows.to_dict(orient="records")
    for r in records:
        if r["years_old"] is not None:
            r["years_old"] = int(r["years_old"])
    payload = {"total": total, "page": page, "page_size": page_size,
               "pages": max(1, math.ceil(total / page_size)), "rows": records}
    API_CACHE.set(key, payload)
    return jsonify(payload)


@app.route("/api/compare")
def api_compare():
    c1 = request.args.get("c1", "").strip().lower()
    c2 = request.args.get("c2", "").strip().lower()
    if not c1 or not c2:
        return jsonify({"error": "Please provide both c1 and c2"}), 400
    key = make_cache_key("compare", f"{data_version()}:{c1}:{c2}")
    cached = API_CACHE.get(key)
    if cached is not None:
        return jsonify(cached)
    df1 = DF[DF["company_name"].str.lower() == c1]
    df2 = DF[DF["company_name"].str.lower() == c2]
    if df1.empty:
        df1 = DF[DF["company_name"].str.lower().str.contains(c1, na=False)]
    if df2.empty:
        df2 = DF[DF["company_name"].str.lower().str.contains(c2, na=False)]

    def clean(df):
        if df.empty:
            return None
        r = df.iloc[0].copy().replace({np.nan: None})
        d = r.to_dict()
        if d.get("years_old") is not None:
            d["years_old"] = int(d["years_old"])
        return d

    payload = {"c1": clean(df1), "c2": clean(df2)}
    API_CACHE.set(key, payload)
    return jsonify(payload)


def _counts(series, top=None):
    vc = series.dropna().value_counts()
    if top:
        vc = vc.head(top)
    return [{"label": str(k), "count": int(v)} for k, v in vc.items()]


@app.route("/api/analytics")
def api_analytics():
    query = request.query_string.decode("utf-8")
    key = make_cache_key("analytics", f"{data_version()}:{query}")
    cached = API_CACHE.get(key)
    if cached is not None:
        return jsonify(cached)

    q = apply_filters(DF)
    rated = q["company_rating"].dropna()
    aged = q["years_old"].dropna()
    top_type = str(q["type"].dropna().value_counts().index[0]) if q["type"].notna().any() else "—"
    kpis = {"total": int(len(q)), "avg_rating": round(float(rated.mean()), 2) if len(rated) else None,
            "avg_years": round(float(aged.mean()), 1) if len(aged) else None,
            "industries": int(q["industry"].nunique()), "locations": int(q["location"].nunique()), "top_type": top_type}
    rating_hist = []
    if len(rated):
        edges = np.arange(1.0, 5.5, 0.5)
        cats = pd.cut(rated, bins=edges, right=True, include_lowest=True)
        for interval, cnt in cats.value_counts().sort_index().items():
            rating_hist.append({"label": f"{interval.left:.1f}–{interval.right:.1f}", "count": int(cnt)})
    years_hist = []
    if len(aged):
        edges = [0, 5, 10, 20, 30, 50, 75, 100, np.inf]
        labels = ["0–5", "6–10", "11–20", "21–30", "31–50", "51–75", "76–100", "100+"]
        cats = pd.cut(aged, bins=edges, labels=labels, right=True, include_lowest=True)
        vc = cats.value_counts().reindex(labels).fillna(0)
        years_hist = [{"label": l, "count": int(c)} for l, c in vc.items()]
    rating_by_industry = []
    if len(q):
        top_inds = q["industry"].dropna().value_counts().head(12).index.tolist()
        sub = q[q["industry"].isin(top_inds)]
        grp = sub.groupby("industry")["company_rating"].mean().reindex(top_inds)
        rating_by_industry = [{"label": str(k), "avg": round(float(v), 2)} for k, v in grp.items() if not pd.isna(v)]
        rating_by_industry.sort(key=lambda d: d["avg"], reverse=True)
    size_counts = q["size"].dropna().value_counts()
    size_dist = [{"label": s, "count": int(size_counts.get(s, 0))}
                 for s in META["filters"]["sizes"] if s in size_counts.index]
    both = q[q["company_rating"].notna() & q["years_old"].notna()]
    if len(both) > 1500:
        both = both.sample(1500, random_state=7)
    scatter = [{"x": int(r.years_old), "y": float(r.company_rating)} for r in both.itertuples()]
    rated_q = q[q["company_rating"].notna()]

    def _avg_by(col, order=None, min_n=20, top=None, sort_desc=False):
        g = rated_q.dropna(subset=[col]).groupby(col)["company_rating"].agg(["mean", "count"])
        keys = [k for k in order if k in g.index] if order is not None else g["count"].sort_values(ascending=False).index.tolist()
        if top:
            keys = keys[:top]
        out = [{"label": str(k), "avg": round(float(g.loc[k, "mean"]), 2), "count": int(g.loc[k, "count"])}
               for k in keys if int(g.loc[k, "count"]) >= min_n]
        if sort_desc:
            out.sort(key=lambda d: d["avg"], reverse=True)
        return out

    rating_by_size = _avg_by("size", [s for s in META["filters"]["sizes"] if "(Global)" not in s], min_n=20)
    rating_by_type = _avg_by("type", None, min_n=15, sort_desc=True)
    rating_by_location = _avg_by("location", None, min_n=30, top=10, sort_desc=True)
    rating_by_age = []
    aged_r = rated_q[rated_q["years_old"].notna()]
    if len(aged_r):
        edges = [0, 5, 10, 20, 30, 50, 75, 100, np.inf]
        labels = ["0–5", "6–10", "11–20", "21–30", "31–50", "51–75", "76–100", "100+"]
        ab = pd.cut(aged_r["years_old"], bins=edges, labels=labels, right=True, include_lowest=True)
        gg = aged_r.groupby(ab, observed=False)["company_rating"].agg(["mean", "count"]).reindex(labels)
        for lab in labels:
            if lab in gg.index and not pd.isna(gg.loc[lab, "mean"]) and gg.loc[lab, "count"] >= 15:
                rating_by_age.append({"label": lab, "avg": round(float(gg.loc[lab, "mean"]), 2), "count": int(gg.loc[lab, "count"])})
    payload = {"kpis": kpis, "top_industries": _counts(q["industry"], top=12), "rating_hist": rating_hist,
               "type_breakdown": _counts(q["type"]), "size_dist": size_dist, "top_locations": _counts(q["location"], top=12),
               "rating_by_industry": rating_by_industry, "years_hist": years_hist, "scatter": scatter,
               "rating_by_size": rating_by_size, "rating_by_type": rating_by_type, "rating_by_age": rating_by_age,
               "rating_by_location": rating_by_location}
    API_CACHE.set(key, payload)
    return jsonify(payload)


@app.route("/api/export")
def api_export():
    q = apply_filters(DF)
    buf = io.StringIO()
    q.to_csv(buf, index=False)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=ambitionbox_filtered.csv"})


register_history_routes(app)


if __name__ == "__main__":
    app.run(debug=AppConfig.DEBUG, host=AppConfig.HOST, port=AppConfig.PORT)
