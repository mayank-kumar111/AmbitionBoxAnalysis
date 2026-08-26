// Dashboard charts, driven by the shared filter panel.
(function () {
  const $ = (s) => document.querySelector(s);

  const isLight = document.documentElement.getAttribute("data-theme") === "light";
  Chart.defaults.color = isLight ? "#475569" : "#93a3bd";
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.borderColor = isLight ? "rgba(15,23,42,.08)" : "rgba(148,163,184,.10)";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.tooltip.backgroundColor = isLight ? "#ffffff" : "#0e1626";
  Chart.defaults.plugins.tooltip.borderColor = isLight ? "#cbd5e1" : "#26375a";
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.titleColor = isLight ? "#0f172a" : "#E2E8F0";
  Chart.defaults.plugins.tooltip.bodyColor = isLight ? "#475569" : "#fff";
  Chart.defaults.plugins.tooltip.cornerRadius = 8;

  const CYAN = "#06B6D4", VIOLET = "#8B5CF6";
  const PIE = ["#06B6D4", "#8B5CF6", "#EC4899", "#34d399", "#fbbf24",
    "#f87171", "#38bdf8", "#a78bfa", "#f472b6", "#22d3ee"];

  function gradient(c1, c2, horizontal) {
    return (context) => {
      const { chart } = context;
      const { ctx, chartArea } = chart;
      if (!chartArea) return c1;
      const g = horizontal
        ? ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0)
        : ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
      g.addColorStop(0, c1); g.addColorStop(1, c2);
      return g;
    };
  }

  const noGridX = { grid: { display: false }, ticks: { autoSkip: false } };
  const softGrid = { grid: { color: isLight ? "rgba(15,23,42,.06)" : "rgba(148,163,184,.08)" }, border: { display: false } };
  // zoomed 3–5 axis so small differences in average rating are actually visible
  const ratingAxis = Object.assign({ min: 3, max: 5, ticks: { stepSize: 0.5 } }, softGrid);
  const avgTip = { callbacks: { label: (c) => {
    const r = c.chart.$rows && c.chart.$rows[c.dataIndex];
    return r ? `★ ${r.avg}  ·  ${r.count.toLocaleString("en-IN")} companies` : c.formattedValue;
  } } };

  const charts = {};

  function init() {
    charts.industries = new Chart($("#c-industries"), {
      type: "bar",
      data: { labels: [], datasets: [{ data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(6,182,212,.55)", "rgba(139,92,246,.95)", true) }] },
      options: { indexAxis: "y", maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: softGrid, y: { grid: { display: false } } },
        onHover: (e, els) => e.native.target.style.cursor = els.length ? 'pointer' : 'default',
        onClick: (e, els) => {
          if (els.length && window.AB && window.AB.ts && window.AB.ts.industry) {
            window.AB.ts.industry.addItem(charts.industries.data.labels[els[0].index]);
          }
        }
      },
    });

    charts.type = new Chart($("#c-type"), {
      type: "doughnut",
      data: { labels: [], datasets: [{ data: [], backgroundColor: PIE, borderColor: "#111b2e", borderWidth: 2 }] },
      options: { maintainAspectRatio: false, cutout: "58%",
        plugins: { legend: { position: "bottom", labels: { boxWidth: 8, padding: 12 } } },
        onHover: (e, els) => e.native.target.style.cursor = els.length ? 'pointer' : 'default',
        onClick: (e, els) => {
          if (els.length && window.AB && window.AB.ts && window.AB.ts.type) {
            window.AB.ts.type.addItem(charts.type.data.labels[els[0].index]);
          }
        }
      },
    });

    charts.rating = new Chart($("#c-rating"), {
      type: "bar",
      data: { labels: [], datasets: [{ label: "Companies", data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(6,182,212,.25)", "rgba(6,182,212,.95)", false) }] },
      options: { maintainAspectRatio: false, plugins: { legend: { display: false } },
        scales: { x: noGridX, y: softGrid } },
    });

    charts.locations = new Chart($("#c-locations"), {
      type: "bar",
      data: { labels: [], datasets: [{ data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(139,92,246,.55)", "rgba(236,72,153,.95)", true) }] },
      options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } },
        scales: { x: softGrid, y: { grid: { display: false } } },
        onHover: (e, els) => e.native.target.style.cursor = els.length ? 'pointer' : 'default',
        onClick: (e, els) => {
          if (els.length && window.AB && window.AB.ts && window.AB.ts.location) {
            window.AB.ts.location.addItem(charts.locations.data.labels[els[0].index]);
          }
        }
      },
    });

    charts.size = new Chart($("#c-size"), {
      type: "bar",
      data: { labels: [], datasets: [{ data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(139,92,246,.3)", "rgba(139,92,246,.95)", false) }] },
      options: { maintainAspectRatio: false, plugins: { legend: { display: false } },
        scales: { x: { grid: { display: false }, ticks: { maxRotation: 55, minRotation: 30 } }, y: softGrid } },
    });

    charts.age = new Chart($("#c-age"), {
      type: "bar",
      data: { labels: [], datasets: [{ data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(52,211,153,.3)", "rgba(6,182,212,.95)", false) }] },
      options: { maintainAspectRatio: false, plugins: { legend: { display: false } },
        scales: { x: noGridX, y: softGrid } },
    });

    charts.rbi = new Chart($("#c-rbi"), {
      type: "bar",
      data: { labels: [], datasets: [{ data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(251,191,36,.6)", "rgba(52,211,153,.95)", true) }] },
      options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false },
        tooltip: { callbacks: { label: (c) => "★ " + c.parsed.x.toFixed(2) } } },
        scales: { x: Object.assign({ min: 0, max: 5 }, softGrid), y: { grid: { display: false } } } },
    });

    charts.scatter = new Chart($("#c-scatter"), {
      type: "scatter",
      data: { datasets: [{ data: [], pointRadius: 3, pointHoverRadius: 5,
        backgroundColor: "rgba(6,182,212,.45)", borderColor: "rgba(139,92,246,.5)" }] },
      options: { maintainAspectRatio: false, plugins: { legend: { display: false },
        tooltip: { callbacks: { label: (c) => `${c.parsed.x} yrs · ★ ${c.parsed.y}` } } },
        scales: {
          x: Object.assign({ title: { display: true, text: "Age (years)" } }, softGrid),
          y: Object.assign({ title: { display: true, text: "Rating" }, min: 1, max: 5 }, softGrid),
        } },
    });

    // ---- rating-driver charts (insights) ----
    charts.rbs = new Chart($("#c-rbs"), {
      type: "bar",
      data: { labels: [], datasets: [{ data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(6,182,212,.35)", "rgba(139,92,246,.95)", false) }] },
      options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: avgTip },
        scales: { x: { grid: { display: false }, ticks: { maxRotation: 55, minRotation: 30 } }, y: ratingAxis } },
    });

    charts.rbt = new Chart($("#c-rbt"), {
      type: "bar",
      data: { labels: [], datasets: [{ data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(251,191,36,.6)", "rgba(52,211,153,.95)", true) }] },
      options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: avgTip },
        scales: { x: ratingAxis, y: { grid: { display: false } } } },
    });

    charts.rba = new Chart($("#c-rba"), {
      type: "line",
      data: { labels: [], datasets: [{ data: [], borderColor: CYAN, borderWidth: 2,
        backgroundColor: "rgba(6,182,212,.14)", fill: true, tension: .35,
        pointRadius: 4, pointBackgroundColor: VIOLET, pointBorderColor: "#0B1120", pointBorderWidth: 2 }] },
      options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: avgTip },
        scales: { x: noGridX, y: ratingAxis } },
    });

    charts.rbl = new Chart($("#c-rbl"), {
      type: "bar",
      data: { labels: [], datasets: [{ data: [], borderRadius: 6, borderSkipped: false,
        backgroundColor: gradient("rgba(139,92,246,.5)", "rgba(6,182,212,.95)", true) }] },
      options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: avgTip },
        scales: { x: ratingAxis, y: { grid: { display: false } } } },
    });
  }

  function setBar(ch, arr, key = "count") {
    ch.$rows = arr;
    ch.data.labels = arr.map(d => d.label);
    ch.data.datasets[0].data = arr.map(d => d[key]);
    ch.update();
  }

  function updateInsight(d) {
    const el = $("#insight-line");
    if (!el) return;
    const bits = [];
    const t = d.rating_by_type || [];
    if (t.length) bits.push(`<b>${t[0].label}</b> companies rate highest at <b>★${t[0].avg}</b>`);
    const a = (d.rating_by_age || []).filter(x => x.count);
    if (a.length >= 2) {
      const first = a[0], last = a[a.length - 1];
      const diff = last.avg - first.avg;
      let trend;
      if (Math.abs(diff) < 0.05) trend = "rating stays remarkably flat as companies age";
      else if (diff > 0) trend = `rating climbs to <b>★${last.avg}</b> for firms ${last.label} yrs old`;
      else trend = `the youngest firms (${first.label} yrs) actually rate best at <b>★${first.avg}</b>`;
      bits.push(trend);
    }
    const loc = d.rating_by_location || [];
    if (loc.length) bits.push(`<b>${loc[0].label}</b> leads the cities (★${loc[0].avg})`);
    el.innerHTML = bits.length ? bits.join(" &nbsp;·&nbsp; ") + "." : "No data for this selection.";
  }

  function refresh(d) {
    const k = d.kpis;
    $("#kpi-total").textContent = k.total.toLocaleString("en-IN");
    $("#kpi-rating").textContent = k.avg_rating != null ? "★ " + k.avg_rating : "—";
    $("#kpi-age").textContent = k.avg_years != null ? k.avg_years + " yr" : "—";
    $("#kpi-ind").textContent = k.industries.toLocaleString("en-IN");
    $("#kpi-type").textContent = k.top_type;
    $("#dash-count").textContent = `Showing ${k.total.toLocaleString("en-IN")} companies.`;

    setBar(charts.industries, d.top_industries);
    setBar(charts.rating, d.rating_hist);
    setBar(charts.locations, d.top_locations);
    setBar(charts.size, d.size_dist);
    setBar(charts.age, d.years_hist);
    setBar(charts.rbi, d.rating_by_industry, "avg");

    charts.type.data.labels = d.type_breakdown.map(x => x.label);
    charts.type.data.datasets[0].data = d.type_breakdown.map(x => x.count);
    charts.type.update();

    charts.scatter.data.datasets[0].data = d.scatter;
    charts.scatter.update();

    setBar(charts.rbs, d.rating_by_size, "avg");
    setBar(charts.rbt, d.rating_by_type, "avg");
    setBar(charts.rba, d.rating_by_age, "avg");
    setBar(charts.rbl, d.rating_by_location, "avg");
    updateInsight(d);
  }

  function buildChips() {
    const p = AB.getParams();
    const chips = [];
    const push = (t) => chips.push(`<span class="chip">${AB.esc(t)}</span>`);
    if (p.get("company_name")) push(`name: "${p.get("company_name")}"`);
    p.getAll("industry").forEach(v => push(v));
    p.getAll("location").forEach(v => push(v));
    p.getAll("size").forEach(v => push(v.replace(" Employees", "")));
    p.getAll("type").forEach(v => push(v));
    if (p.get("rating_min") || p.get("rating_max"))
      push(`★ ${p.get("rating_min") || "1.0"}–${p.get("rating_max") || "5.0"}`);
    if (p.get("years_min") || p.get("years_max"))
      push(`age ${p.get("years_min") || "0"}–${p.get("years_max") || (AB.yCap || AB.meta.filters.years.max) + "+"}`);
    $("#filter-chips").innerHTML = chips.length
      ? chips.join("") : `<span class="muted">none — showing all companies</span>`;
  }

  let loadTok = 0;
  async function load() {
    buildChips();
    const tok = ++loadTok;
    const d = await fetch("/api/analytics?" + AB.getParams().toString()).then(r => r.json());
    if (tok !== loadTok) return;
    refresh(d);
  }

  const drawer = $("#drawer"), scrim = $("#scrim");
  const openD = () => { drawer.classList.add("open"); scrim.classList.add("open"); };
  const closeD = () => { drawer.classList.remove("open"); scrim.classList.remove("open"); };
  $("#open-filters").addEventListener("click", openD);
  $("#close-filters").addEventListener("click", closeD);
  scrim.addEventListener("click", closeD);

  init();
  AB.initFilters($("#filter-panel"), load).then(load);
  window.addEventListener("themeChanged", (e) => {
    const isLight = e.detail.theme === "light";
    Chart.defaults.color = isLight ? "#475569" : "#93a3bd";
    Chart.defaults.borderColor = isLight ? "rgba(15,23,42,.08)" : "rgba(148,163,184,.10)";
    Chart.defaults.plugins.tooltip.backgroundColor = isLight ? "#ffffff" : "#0e1626";
    Chart.defaults.plugins.tooltip.borderColor = isLight ? "#cbd5e1" : "#26375a";
    Chart.defaults.plugins.tooltip.titleColor = isLight ? "#0f172a" : "#E2E8F0";
    Chart.defaults.plugins.tooltip.bodyColor = isLight ? "#475569" : "#fff";

    softGrid.grid.color = isLight ? "rgba(15,23,42,.06)" : "rgba(148,163,184,.08)";

    for (const key in charts) {
      const c = charts[key];
      if (c.options.scales) {
        if (c.options.scales.x && c.options.scales.x.grid) c.options.scales.x.grid.color = softGrid.grid.color;
        if (c.options.scales.y && c.options.scales.y.grid) c.options.scales.y.grid.color = softGrid.grid.color;
      }
      c.update();
    }
  });

})();
