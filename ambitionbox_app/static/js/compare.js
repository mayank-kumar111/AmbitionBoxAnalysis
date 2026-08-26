(function () {
  const $ = (s) => document.querySelector(s);
  const esc = window.AB && window.AB.esc ? window.AB.esc : (v) => {
    const el = document.createElement("div");
    el.textContent = String(v);
    return el.innerHTML;
  };

  let c1Name = null;
  let c2Name = null;

  function setupSearch(inputId, dropdownId, onSelect) {
    const input = $(inputId);
    const dropdown = $(dropdownId);
    let timer = null;

    input.addEventListener("input", () => {
      clearTimeout(timer);
      const val = input.value.trim();
      if (!val) { dropdown.style.display = "none"; return; }
      timer = setTimeout(async () => {
        try {
          const d = await fetch(`/api/companies?company_name=${encodeURIComponent(val)}&page_size=5`).then(r => r.json());
          if (!d.rows.length) {
            dropdown.innerHTML = `<div class="sr-empty">No matching companies</div>`;
          } else {
            dropdown.innerHTML = d.rows.map(r => 
              `<div class="sr-item" data-name="${esc(r.company_name)}">
                 <div class="sr-name">${esc(r.company_name)}</div>
                 <div class="sr-meta">★ ${r.company_rating || "—"} · ${esc(r.industry || "Unknown")}</div>
               </div>`
            ).join("");
          }
          dropdown.style.display = "block";
        } catch (err) {
          console.error(err);
        }
      }, 250);
    });

    dropdown.addEventListener("click", (e) => {
      const item = e.target.closest(".sr-item");
      if (item) {
        input.value = item.dataset.name;
        dropdown.style.display = "none";
        onSelect(item.dataset.name);
      }
    });

    document.addEventListener("click", (e) => {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = "none";
      }
    });
  }

  function renderTable(d) {
    if (!d.c1 && !d.c2) return;
    
    $("#compare-empty").style.display = "none";
    $("#compare-results").style.display = "block";
    
    $("#c1-name-th").textContent = d.c1 ? d.c1.company_name : c1Name;
    $("#c2-name-th").textContent = d.c2 ? d.c2.company_name : c2Name;
    
    const v = (obj, key, fmt = x => x) => {
      if (!obj || obj[key] == null) return '<span class="dash">—</span>';
      return esc(fmt(obj[key]));
    };

    const c1 = d.c1;
    const c2 = d.c2;

    const r1 = c1 ? parseFloat(c1.company_rating) || 0 : 0;
    const r2 = c2 ? parseFloat(c2.company_rating) || 0 : 0;
    const a1 = c1 ? parseInt(c1.years_old) || 0 : 0;
    const a2 = c2 ? parseInt(c2.years_old) || 0 : 0;
    
    let score1 = 0;
    let score2 = 0;
    
    if (r1 > r2) score1++; else if (r2 > r1) score2++;
    if (a1 > a2) score1++; else if (a2 > a1) score2++;
    
    let c1Crown = "", c2Crown = "";
    if (score1 > score2) c1Crown = `<div class="compare-crown">👑</div>`;
    else if (score2 > score1) c2Crown = `<div class="compare-crown">👑</div>`;

    $("#c1-name-th").innerHTML = `${c1Crown}${c1 ? c1.company_name : c1Name} <span class="compare-score">${score1 > score2 ? 'Overall Winner' : ''}</span>`;
    $("#c2-name-th").innerHTML = `${c2Crown}${c2 ? c2.company_name : c2Name} <span class="compare-score">${score2 > score1 ? 'Overall Winner' : ''}</span>`;
    
    // helper to highlight the winner
    const cell = (val1, val2, val1_raw, val2_raw, higherIsBetter = true) => {
      let c1_class = "", c2_class = "";
      if (val1_raw != null && val2_raw != null) {
        if (val1_raw > val2_raw) {
          c1_class = higherIsBetter ? "winner" : "loser";
          c2_class = higherIsBetter ? "loser" : "winner";
        } else if (val2_raw > val1_raw) {
          c2_class = higherIsBetter ? "winner" : "loser";
          c1_class = higherIsBetter ? "loser" : "winner";
        }
      }
      return `
        <td class="center-td ${c1_class}">${val1}</td>
        <td class="center-td ${c2_class}">${val2}</td>
      `;
    };

    const ratingBar = (val, raw) => {
      if (!val || val.includes("—")) return cell(val, val, 0, 0);
      const pct = (raw / 5) * 100;
      return `<div style="position:relative; width: 100px; height:6px; background:var(--panel-2); border-radius:3px; margin: 8px auto 0; overflow:hidden;">
                <div style="position:absolute; top:0; left:0; height:100%; width:${pct}%; background:var(--cyan); border-radius:3px;"></div>
              </div>`;
    };

    const ageBar = (raw1, raw2, raw) => {
      if (!raw) return "";
      const maxAge = Math.max(raw1, raw2, 1);
      const pct = (raw / maxAge) * 100;
      return `<div style="position:relative; width: 100px; height:6px; background:var(--panel-2); border-radius:3px; margin: 8px auto 0; overflow:hidden;">
                <div style="position:absolute; top:0; left:0; height:100%; width:${pct}%; background:var(--violet); border-radius:3px;"></div>
              </div>`;
    };

    const rows = [
      `<tr>
         <td class="lbl">Overall Rating</td>
         ${cell(v(c1, 'company_rating', x=>"★ "+x) + ratingBar(c1?'1':null, r1), 
                v(c2, 'company_rating', x=>"★ "+x) + ratingBar(c2?'1':null, r2), 
                r1, r2, true)}
       </tr>`,
      `<tr>
         <td class="lbl">Industry</td>
         <td class="center-td">${v(c1, 'industry')}</td>
         <td class="center-td">${v(c2, 'industry')}</td>
       </tr>`,
      `<tr>
         <td class="lbl">Company Type</td>
         <td class="center-td">${v(c1, 'type')}</td>
         <td class="center-td">${v(c2, 'type')}</td>
       </tr>`,
      `<tr>
         <td class="lbl">Size</td>
         <td class="center-td">${v(c1, 'size')}</td>
         <td class="center-td">${v(c2, 'size')}</td>
       </tr>`,
      `<tr>
         <td class="lbl">Age</td>
         ${cell(v(c1, 'years_old', x=>x+" yrs") + ageBar(a1, a2, a1), 
                v(c2, 'years_old', x=>x+" yrs") + ageBar(a1, a2, a2), 
                a1, a2, true)}
       </tr>`,
      `<tr>
         <td class="lbl">Headquarters</td>
         <td class="center-td">${v(c1, 'location')}</td>
         <td class="center-td">${v(c2, 'location')}</td>
       </tr>`
    ];

    $("#compare-tbody").innerHTML = rows.join("");
  }

  async function fetchCompare() {
    if (!c1Name || !c2Name) return;
    try {
      const d = await fetch(`/api/compare?c1=${encodeURIComponent(c1Name)}&c2=${encodeURIComponent(c2Name)}`).then(r => r.json());
      if (d.error) {
        console.error(d.error);
        return;
      }
      renderTable(d);
    } catch (err) {
      console.error(err);
    }
  }

  setupSearch("#c1-input", "#c1-dropdown", (name) => {
    c1Name = name;
    fetchCompare();
  });

  setupSearch("#c2-input", "#c2-dropdown", (name) => {
    c2Name = name;
    fetchCompare();
  });

})();
