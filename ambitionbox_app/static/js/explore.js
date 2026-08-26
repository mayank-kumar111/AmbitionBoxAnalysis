// Explore page: filterable, sortable, paginated company table.
(function () {
  const state = { page: 1, page_size: 25, sort: "company_rating", order: "desc" };
  const $ = (s) => document.querySelector(s);
  const esc = AB.esc;

  function ratingCell(v) {
    if (v === null || v === undefined) return `<span class="rating na">—</span>`;
    const cls = v >= 4 ? "hi" : v >= 3 ? "mid" : "lo";
    return `<span class="rating ${cls}">★ ${(+v).toFixed(1)}</span>`;
  }
  const cell = (v) => (v === null || v === undefined || v === "")
    ? `<span class="dash">—</span>` : esc(v);

  function skeletonRows(n = 10) {
    let h = "";
    for (let i = 0; i < n; i++)
      h += `<tr>${"<td><div class='skeleton' style='height:16px'></div></td>".repeat(7)}</tr>`;
    $("#rows").innerHTML = h;
  }

  function render(data) {
    $("#result-total").textContent = data.total.toLocaleString("en-IN");
    if (!data.rows.length) {
      $("#rows").innerHTML =
        `<tr data-empty="1"><td colspan="7"><div class="empty"><div class="big"><svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div>
         No companies match these filters.<br><span class="muted">Try widening your criteria or resetting.</span></div></td></tr>`;
      $("#pager").innerHTML = "";
      return;
    }
    $("#rows").innerHTML = data.rows.map(r => {
      const q = encodeURIComponent(r.company_name + " ambitionbox");
      const info = encodeURIComponent(JSON.stringify(r));
      return `<tr data-info="${info}">
        <td class="co-name"><a href="https://www.google.com/search?q=${q}" target="_blank" rel="noopener">${esc(r.company_name)}</a></td>
        <td>${ratingCell(r.company_rating)}</td>
        <td>${r.industry ? `<span class="pill">${esc(r.industry)}</span>` : cell(null)}</td>
        <td>${cell(r.size ? String(r.size).replace(" Employees", "") : null)}</td>
        <td>${r.type ? `<span class="pill">${esc(r.type)}</span>` : cell(null)}</td>
        <td>${r.years_old !== null ? esc(r.years_old) + " yr" : cell(null)}</td>
        <td>${cell(r.location)}</td>
      </tr>`;
    }).join("");
    renderPager(data);
  }

  $("#rows").addEventListener("click", (e) => {
    const tr = e.target.closest("tr");
    if (!tr || tr.dataset.empty) return;
    if (e.target.tagName === "A" || e.target.closest("a")) return;
    
    try {
      const data = JSON.parse(decodeURIComponent(tr.dataset.info || "%7B%7D"));
      if (window.openCompanyModal) window.openCompanyModal(data);
    } catch(err) {
      console.error(err);
    }
  });

  function renderPager(data) {
    const { page, pages } = data;
    if (pages <= 1) { $("#pager").innerHTML = ""; return; }
    const btn = (p, label = p, active = false, disabled = false) =>
      `<button ${disabled ? "disabled" : ""} class="${active ? "active" : ""}" data-page="${p}">${label}</button>`;
    let h = btn(page - 1, "‹", false, page === 1);
    const win = [];
    const push = (p) => { if (p >= 1 && p <= pages && !win.includes(p)) win.push(p); };
    push(1); push(2);
    for (let p = page - 1; p <= page + 1; p++) push(p);
    push(pages - 1); push(pages);
    win.sort((a, b) => a - b);
    let prev = 0;
    win.forEach(p => {
      if (p - prev > 1) h += `<span class="info">…</span>`;
      h += btn(p, p, p === page);
      prev = p;
    });
    h += btn(page + 1, "›", false, page === pages);
    h += `<span class="info">${data.total.toLocaleString("en-IN")} total</span>`;
    $("#pager").innerHTML = h;
    $("#pager").querySelectorAll("button[data-page]").forEach(b =>
      b.addEventListener("click", () => { state.page = +b.dataset.page; load(false); window.scrollTo({ top: 0, behavior: "smooth" }); }));
  }

  async function load(resetPage = true) {
    if (resetPage) state.page = 1;
    skeletonRows();
    const p = AB.getParams();
    p.set("page", state.page);
    p.set("page_size", state.page_size);
    p.set("sort", state.sort);
    p.set("order", state.order);
    const data = await fetch("/api/companies?" + p.toString()).then(r => r.json());
    render(data);
  }

  function updateSortArrows() {
    document.querySelectorAll("th[data-sort] .arrow").forEach(a => a.textContent = "");
    const th = document.querySelector(`th[data-sort="${state.sort}"] .arrow`);
    if (th) th.textContent = state.order === "asc" ? "▲" : "▼";
  }

  document.querySelectorAll("th[data-sort]").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.sort;
      if (state.sort === col) state.order = state.order === "asc" ? "desc" : "asc";
      else { state.sort = col; state.order = col === "company_name" || col === "location" || col === "industry" ? "asc" : "desc"; }
      updateSortArrows();
      load(false);
    });
  });

  $("#page-size").addEventListener("change", (e) => { state.page_size = +e.target.value; load(true); });

  $("#export-csv").addEventListener("click", () => {
    const p = AB.getParams();
    p.set("sort", state.sort);
    p.set("order", state.order);
    window.location.href = "/api/export?" + p.toString();
  });

  // Boot
  AB.initFilters($("#filter-panel"), () => load(true)).then(() => {
    updateSortArrows();
    load(true);
  });
})();
