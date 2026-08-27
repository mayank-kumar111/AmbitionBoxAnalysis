(function() {
  const input = document.getElementById("global-search-input");
  const dropdown = document.getElementById("global-search-results");
  const esc = window.AB && window.AB.esc ? window.AB.esc : (s) => String(s).replace(/[&<>"']/g, function(m) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m]; });

  window.openCompanyModal = function(data) {
    const $ = (s) => document.querySelector(s);
    $("#modal-title").textContent = data.company_name;
    $("#modal-rating-val").textContent = data.company_rating ? Number(data.company_rating).toFixed(1) : "N/A";
    let tags = "";
    if (data.industry) tags += `<span>${esc(data.industry)}</span>`;
    if (data.type) tags += `<span>${esc(data.type)}</span>`;
    if (data.location) tags += `<span>${esc(data.location)}</span>`;
    if (data.size) tags += `<span>${esc(String(data.size).replace(" Employees", ""))}</span>`;
    $("#modal-tags").innerHTML = tags;
    let b = `<strong>${esc(data.company_name)}</strong> is a ${data.years_old ? data.years_old+' year old ' : ''}company`;
    if (data.location) b += ` based in ${esc(data.location)}.`;
    else b += ".";
    if (data.company_rating >= 4.0) b += `<br><br><span style="color:var(--cyan)">★ This company is highly rated!</span>`;
    $("#modal-body").innerHTML = b;
    $("#company-modal").classList.add("active");
  };

  function openCompanyHistory(data) {
    const params = new URLSearchParams({ name: data.company_name });
    if (data.location) params.set("location", data.location);
    window.location.href = `/history/company?${params.toString()}`;
  }

  if (!input || !dropdown) return;

  let debounceTimer;

  input.addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    const q = e.target.value.trim();
    if (q.length < 2) {
      dropdown.classList.remove("active");
      dropdown.innerHTML = "";
      return;
    }
    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/companies?company_name=${encodeURIComponent(q)}&page=1&page_size=8`);
        const data = await res.json();
        if (data.rows.length === 0) {
          dropdown.innerHTML = `<div class="search-empty">No companies found</div>`;
        } else {
          dropdown.innerHTML = data.rows.map(r => {
            const info = encodeURIComponent(JSON.stringify(r));
            return `<div class="search-item" data-info="${info}">
              <div class="search-item-title">${esc(r.company_name)} <span>★ ${r.company_rating ? Number(r.company_rating).toFixed(1) : '-'}</span></div>
              <div class="search-item-sub">${r.industry ? esc(r.industry) : ''}${r.location ? ' · ' + esc(r.location) : ''}</div>
              <div class="search-item-actions"><button type="button" class="search-history-btn">View history</button></div>
            </div>`;
          }).join("");
        }
        dropdown.classList.add("active");
      } catch(err) {
        console.error(err);
      }
    }, 300);
  });

  dropdown.addEventListener("click", (e) => {
    const item = e.target.closest(".search-item");
    if (!item) return;
    try {
      const data = JSON.parse(decodeURIComponent(item.dataset.info || "%7B%7D"));
      dropdown.classList.remove("active");
      input.value = "";
      if (e.target.closest(".search-history-btn")) {
        openCompanyHistory(data);
        return;
      }
      window.openCompanyModal(data);
    } catch(err) {}
  });

  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove("active");
    }
  });
})();
