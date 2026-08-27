(function () {
  const $ = (s) => document.querySelector(s);

  function number(value) {
    return Number(value || 0).toLocaleString("en-IN");
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    }[c]));
  }

  function renderTable(target, rows, columns) {
    const el = $(target);
    if (!el) return;
    if (!rows.length) {
      el.innerHTML = '<p class="muted">No history records available yet.</p>';
      return;
    }
    el.innerHTML = `<table class="data-table"><thead><tr>${columns.map(c => `<th>${escapeHtml(c.label)}</th>`).join("")}</tr></thead><tbody>` +
      rows.map(row => `<tr>${columns.map(c => `<td>${escapeHtml(c.format ? c.format(row) : row[c.key])}</td>`).join("")}</tr>`).join("") +
      '</tbody></table>';
  }

  async function load() {
    try {
      const response = await fetch("/api/history");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      $("#history-companies").textContent = number(data.current_companies);
      $("#history-snapshots").textContent = number(data.snapshot_count);
      $("#history-new").textContent = number(data.new_records);
      $("#history-updates").textContent = number(data.rating_updates);
      $("#history-status").textContent = data.latest_snapshot
        ? `Latest snapshot: ${data.latest_snapshot}`
        : "No snapshots recorded yet.";

      const latest = $("#history-latest");
      latest.innerHTML = data.latest_activity.length
        ? data.latest_activity.map(x => `<div style="padding:9px 0;border-bottom:1px solid var(--border)"><b>${escapeHtml(x.company_name)}</b><br><span class="muted">${escapeHtml(x.change_type)} · ${escapeHtml(x.snapshot_at)}</span></div>`).join("")
        : '<p class="muted">No activity recorded.</p>';

      renderTable("#history-improved", data.improved_companies, [
        { label: "Company", key: "company_name" },
        { label: "Location", key: "location" },
        { label: "Rating change", format: r => `+${r.change.toFixed(2)}` }
      ]);

      renderTable("#history-new-list", data.latest_new, [
        { label: "Company", key: "company_name" },
        { label: "Location", key: "location" },
        { label: "Discovered", key: "snapshot_at" }
      ]);

      const ctx = $("#history-growth");
      if (ctx && data.growth.length && typeof Chart !== "undefined") {
        new Chart(ctx, {
          type: "line",
          data: {
            labels: data.growth.map(x => x.snapshot_at),
            datasets: [{ label: "Companies in snapshot", data: data.growth.map(x => x.companies), tension: 0.3, fill: true }]
          },
          options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: false } } }
        });
      }
    } catch (error) {
      console.error("History load failed:", error);
      const status = $("#history-status");
      if (status) status.textContent = "History database unavailable.";
    }
  }

  document.addEventListener("DOMContentLoaded", load);
})();
