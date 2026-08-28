(function () {
  const $ = (s) => document.querySelector(s);
  const state = { chartGrowth: null, chartActivity: null };

  function number(value) {
    return Number(value || 0).toLocaleString("en-IN");
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    }[c]));
  }

  function renderTable(target, rows, columns, empty = "No history records available yet.") {
    const el = $(target);
    if (!el) return;
    if (!rows.length) {
      el.innerHTML = `<p class="muted">${escapeHtml(empty)}</p>`;
      return;
    }
    el.innerHTML = `<table class="data-table"><thead><tr>${columns.map(c => `<th>${escapeHtml(c.label)}</th>`).join("")}</tr></thead><tbody>` +
      rows.map(row => `<tr>${columns.map(c => `<td>${escapeHtml(c.format ? c.format(row) : row[c.key])}</td>`).join("")}</tr>`).join("") +
      '</tbody></table>';
  }

  function renderCharts(data, refreshRuns) {
    if (typeof Chart === "undefined") return;

    const growthCtx = $("#history-growth");
    if (growthCtx) {
      if (state.chartGrowth) state.chartGrowth.destroy();
      state.chartGrowth = new Chart(growthCtx, {
        type: "line",
        data: {
          labels: data.growth.map(x => x.snapshot_at),
          datasets: [{
            label: "Companies",
            data: data.growth.map(x => x.companies),
            tension: 0.3,
            fill: true
          }]
        },
        options: {
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: false } }
        }
      });
    }

    const activityCtx = $("#refresh-activity");
    if (activityCtx) {
      if (state.chartActivity) state.chartActivity.destroy();
      state.chartActivity = new Chart(activityCtx, {
        type: "bar",
        data: {
          labels: refreshRuns.map(x => x.snapshot_at),
          datasets: [
            { label: "New", data: refreshRuns.map(x => x.new_records) },
            { label: "Updated", data: refreshRuns.map(x => x.updated_records) },
            { label: "Duplicates", data: refreshRuns.map(x => x.duplicate_records) },
            { label: "Invalid", data: refreshRuns.map(x => x.invalid_records) }
          ]
        },
        options: {
          maintainAspectRatio: false,
          responsive: true,
          scales: { y: { beginAtZero: true } }
        }
      });
    }
  }

  async function load() {
    try {
      const response = await fetch("/api/history");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      let refreshRuns = Array.isArray(data.refresh_runs) ? data.refresh_runs : [];
      if (!refreshRuns.length) {
        try {
          const staticResponse = await fetch("/static/refresh_history.json", { cache: "no-store" });
          if (staticResponse.ok) {
            const payload = await staticResponse.json();
            refreshRuns = Array.isArray(payload.runs) ? payload.runs : [];
          }
        } catch (_) {}
      }

      $("#history-companies").textContent = number(data.current_companies);
      $("#history-snapshots").textContent = number(data.snapshot_count);
      $("#history-runs").textContent = number(data.refresh_run_count || refreshRuns.length);
      $("#history-updates").textContent = number(data.rating_updates);
      $("#history-status").textContent = data.latest_snapshot
        ? `Latest snapshot: ${data.latest_snapshot}`
        : "No snapshots recorded yet.";

      renderTable("#refresh-runs-table", refreshRuns.slice().reverse(), [
        { label: "Snapshot", key: "snapshot_at" },
        { label: "Previous", format: r => number(r.previous_records) },
        { label: "Incoming", format: r => number(r.incoming_records) },
        { label: "Final", format: r => number(r.final_records) },
        { label: "New", format: r => number(r.new_records) },
        { label: "Updated", format: r => number(r.updated_records) },
        { label: "Duplicates", format: r => number(r.duplicate_records) },
        { label: "Collapsed", format: r => number(r.collapsed_records) },
        { label: "Invalid", format: r => number(r.invalid_records) },
        { label: "Mode", format: r => Number(r.applied) ? "Applied" : "Dry run" }
      ], "No refresh runs have been recorded yet.");

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

      renderCharts(data, refreshRuns);
    } catch (error) {
      console.error("History load failed:", error);
      const status = $("#history-status");
      if (status) status.textContent = "History database unavailable.";
    }
  }

  document.addEventListener("DOMContentLoaded", load);
})();
