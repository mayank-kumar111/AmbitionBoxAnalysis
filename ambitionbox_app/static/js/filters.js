// Shared filter panel for the explore and dashboard pages.
window.AB = window.AB || {};

AB.meta = null;
AB.ts = {};        // tom-select instances
AB.sliders = {};   // noUiSlider elements
AB._onChange = null;
AB._timer = null;

AB._debounced = function () {
  clearTimeout(AB._timer);
  AB._timer = setTimeout(() => AB._onChange && AB._onChange(), 260);
};

AB.fetchMeta = async function () {
  if (AB.meta) return AB.meta;
  AB.meta = await fetch("/api/meta").then(r => r.json());
  return AB.meta;
};

AB._opts = (arr) => arr.map(v => `<option value="${AB.esc(v)}">${AB.esc(v)}</option>`).join("");
AB.esc = (s) => String(s).replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

AB.initFilters = async function (container, onChange) {
  AB._onChange = onChange;
  const m = await AB.fetchMeta();
  const yMax = m.filters.years.max;
  const yCap = Math.min(150, yMax);   // cap slider so a lone 546-yr outlier doesn't stretch it
  AB.yCap = yCap;

  container.innerHTML = `
    <div class="fhead" style="display:flex;align-items:center">
      <h2>Filters</h2>
      <span class="reset" id="f-reset">Reset all</span>
    </div>

    <div class="fgroup">
      <label>Company name</label>
      <input class="f-input" id="f-name" type="text" placeholder="Search a company…" autocomplete="off">
    </div>

    <div class="fgroup">
      <label>Industry</label>
      <select id="f-industry" multiple placeholder="All industries">${AB._opts(m.filters.industries)}</select>
    </div>

    <div class="fgroup">
      <label>Location</label>
      <select id="f-location" multiple placeholder="All locations">${AB._opts(m.filters.locations)}</select>
    </div>

    <div class="fgroup">
      <label>Company size</label>
      <select id="f-size" multiple placeholder="All sizes">${AB._opts(m.filters.sizes)}</select>
    </div>

    <div class="fgroup">
      <label>Type</label>
      <select id="f-type" multiple placeholder="All types">${AB._opts(m.filters.types)}</select>
    </div>

    <div class="fgroup">
      <label>Rating <span class="range-val" id="f-rating-val">1.0 – 5.0</span></label>
      <div class="slider" id="f-rating"></div>
    </div>

    <div class="fgroup">
      <label>Age (years) <span class="range-val" id="f-years-val">0 – ${yCap}+</span></label>
      <div class="slider" id="f-years"></div>
      <label class="check"><input type="checkbox" id="f-unknown" checked> Include companies with unknown age</label>
    </div>

    <div class="actions">
      <a class="btn btn-ghost btn-sm" id="f-export" href="#">Export CSV</a>
    </div>
  `;

  // Tom Select multiselects
  const tsCfg = { plugins: ["remove_button"], maxOptions: 500, hideSelected: true };
  ["industry", "location", "size", "type"].forEach(k => {
    AB.ts[k] = new TomSelect(container.querySelector(`#f-${k}`),
      Object.assign({}, tsCfg, { onChange: AB._debounced }));
  });

  // Rating slider (linear 1–5)
  const rating = container.querySelector("#f-rating");
  noUiSlider.create(rating, {
    start: [1, 5], connect: true, step: 0.1, range: { min: 1, max: 5 },
  });
  AB.sliders.rating = rating;
  rating.noUiSlider.on("update", (v) => {
    container.querySelector("#f-rating-val").textContent =
      `${(+v[0]).toFixed(1)} – ${(+v[1]).toFixed(1)}`;
  });
  rating.noUiSlider.on("change", AB._debounced);

  // Age slider (non-linear — more resolution at the low end where most data sits)
  const years = container.querySelector("#f-years");
  noUiSlider.create(years, {
    start: [0, yCap], connect: true, step: 1,
    range: { min: 0, "25%": 10, "50%": 25, "75%": 60, max: yCap },
  });
  AB.sliders.years = years;
  years.noUiSlider.on("update", (v) => {
    const hi = Math.round(v[1]);
    container.querySelector("#f-years-val").textContent =
      `${Math.round(v[0])} – ${hi >= yCap ? yCap + "+" : hi}`;
  });
  years.noUiSlider.on("change", AB._debounced);

  // Name search + unknown toggle
  container.querySelector("#f-name").addEventListener("input", AB._debounced);
  container.querySelector("#f-unknown").addEventListener("change", AB._debounced);

  // Export current selection
  container.querySelector("#f-export").addEventListener("click", (e) => {
    e.preventDefault();
    window.location = "/api/export?" + AB.getParams().toString();
  });

  // Reset
  container.querySelector("#f-reset").addEventListener("click", AB.reset);
};

AB.getParams = function () {
  const p = new URLSearchParams();
  const m = AB.meta;

  const name = document.querySelector("#f-name").value.trim();
  if (name) p.set("company_name", name);

  ["industry", "location", "size", "type"].forEach(k => {
    (AB.ts[k].getValue() || []).forEach(v => v && p.append(k, v));
  });

  const [rlo, rhi] = AB.sliders.rating.noUiSlider.get().map(Number);
  if (rlo > 1.0001) p.set("rating_min", rlo.toFixed(1));
  if (rhi < 4.9999) p.set("rating_max", rhi.toFixed(1));

  const [ylo, yhi] = AB.sliders.years.noUiSlider.get().map(Number);
  const yCap = AB.yCap || Math.min(150, m.filters.years.max);
  if (ylo > 0.5) p.set("years_min", Math.round(ylo));
  if (yhi < yCap - 0.5) p.set("years_max", Math.round(yhi));

  if (!document.querySelector("#f-unknown").checked) p.set("include_unknown_age", "false");
  return p;
};

AB.reset = function () {
  document.querySelector("#f-name").value = "";
  ["industry", "location", "size", "type"].forEach(k => AB.ts[k].clear());
  AB.sliders.rating.noUiSlider.set([1, 5]);
  AB.sliders.years.noUiSlider.set([0, AB.yCap || Math.min(150, AB.meta.filters.years.max)]);
  document.querySelector("#f-unknown").checked = true;
  AB._onChange && AB._onChange();
};
