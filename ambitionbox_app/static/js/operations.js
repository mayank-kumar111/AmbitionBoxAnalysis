(function () {
  const esc = (value) => String(value ?? "—")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const fmt = (value) => value == null ? "—" : Number(value).toLocaleString("en-IN");
  const dt = (value) => value == null ? "—" : new Date(Number(value) * 1000).toLocaleString("en-IN");

  function render(data) {
    const health = data.latest_refresh?.health || {};
    const alerts = data.latest_refresh?.alerts || {};
    const metrics = data.latest_refresh?.metrics || {};
    const score = health.score == null ? "—" : `${health.score}/100`;
    const status = health.status || "No refresh report";
    const badge = status.toLowerCase();

    document.getElementById("ops-health").innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:20px;align-items:center;flex-wrap:wrap;">
        <div><div class="muted" style="font-size:.82rem;">Pipeline health</div><strong style="font-size:1.55rem;">${esc(status)}</strong></div>
        <div style="font-size:1.4rem;font-weight:700;">${esc(score)}</div>
        <div class="muted">Warnings: ${fmt(health.warning_count ?? health.warnings)} · Critical: ${fmt(health.critical_count ?? health.critical)}</div>
      </div>`;

    document.getElementById("ops-master").innerHTML = data.master?.exists
      ? `<strong>${fmt(data.latest_refresh?.metrics?.final_records ?? data.database?.companies)}</strong> records<br><span class="muted">Updated: ${esc(dt(data.master.modified_at))}</span><br><span class="muted">File size: ${fmt(Math.round((data.master.size || 0) / 1024))} KB</span>`
      : `<span>Master CSV not found.</span>`;

    document.getElementById("ops-db").innerHTML = data.database?.exists
      ? `<strong>${fmt(data.database.companies)}</strong> companies<br><span class="muted">${fmt(data.database.snapshots)} snapshots · ${fmt(data.database.refresh_runs)} refresh runs</span><br><span class="muted">Latest: ${esc(data.database.latest_snapshot)}</span>`
      : `<span>SQLite database not found.</span>`;

    document.getElementById("ops-refresh").innerHTML = `
      <strong>${esc(status)}</strong><br>
      <span class="muted">Incoming: ${fmt(metrics.incoming_records)} · Final: ${fmt(metrics.final_records)}</span><br>
      <span class="muted">New: ${fmt(metrics.new_records)} · Updated: ${fmt(metrics.updated_records)} · Duplicates: ${fmt(metrics.duplicate_records)}</span><br>
      <span class="muted">Applied: ${metrics.applied == null ? "—" : esc(metrics.applied)}</span>`;

    const backups = data.backups || [];
    document.getElementById("ops-backups").innerHTML = backups.length
      ? `<strong>${backups.length}</strong> recent master backup(s)<br><span class="muted">Latest: ${esc(backups[0].name)}</span>`
      : `<span>No master CSV backups found.</span>`;

    const items = Array.isArray(alerts.items) ? alerts.items : [];
    const anomalyItems = Array.isArray(data.latest_refresh?.anomalies) ? data.latest_refresh.anomalies : [];
    const combined = items.length ? items : anomalyItems;
    document.getElementById("ops-alerts").innerHTML = combined.length
      ? combined.slice(0, 8).map((a) => `<div style="padding:10px 0;border-bottom:1px solid var(--border);"><strong>${esc(a.code || a.type || a.severity || "Alert")}</strong><div class="muted" style="margin-top:3px;">${esc(a.message || a.reason || "Anomaly detected")}</div></div>`).join("")
      : `<span class="muted">No alerts in the latest refresh report.</span>`;
  }

  async function load() {
    try {
      const response = await fetch("/api/ops", { cache: "no-store" });
      if (!response.ok) throw new Error("Operations API unavailable");
      render(await response.json());
    } catch (error) {
      document.getElementById("ops-health").textContent = "Unable to load operations status.";
    }
  }

  load();
  window.setInterval(load, 10000);
})();
