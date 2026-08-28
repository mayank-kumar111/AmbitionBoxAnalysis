// Safe refresh control for local Flask use.
(function () {
  const panel = document.createElement("div");
  panel.id = "refresh-control";
  panel.innerHTML = `
    <button type="button" id="refresh-toggle" title="Refresh AmbitionBox data">↻ Refresh</button>
    <div id="refresh-menu" hidden>
      <div class="refresh-title">Refresh dataset</div>
      <label>Pages
        <select id="refresh-pages">
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="5">5</option>
        </select>
      </label>
      <div class="refresh-grid">
        <button data-extended="false" data-apply="false">Core · Dry run</button>
        <button data-extended="false" data-apply="true">Core · Apply</button>
        <button data-extended="true" data-apply="false">Extended · Dry run</button>
        <button data-extended="true" data-apply="true">Extended · Apply</button>
      </div>
      <div id="refresh-status" class="refresh-status">Ready</div>
      <div id="refresh-result" class="refresh-result" hidden></div>
      <div class="refresh-history-title">Recent refreshes</div>
      <div id="refresh-history" class="refresh-history"><span class="muted">Loading…</span></div>
    </div>`;
  document.body.appendChild(panel);

  const style = document.createElement("style");
  style.textContent = `
    #refresh-control{position:fixed;right:22px;bottom:22px;z-index:9999;font-family:Inter,system-ui,sans-serif}
    #refresh-toggle{border:1px solid rgba(148,163,184,.22);background:rgba(15,23,42,.92);color:#e2e8f0;border-radius:10px;padding:10px 14px;font-weight:700;cursor:pointer;box-shadow:0 8px 28px rgba(0,0,0,.22)}
    #refresh-menu{margin-top:8px;width:340px;max-height:75vh;overflow:auto;padding:14px;border:1px solid rgba(148,163,184,.18);border-radius:12px;background:rgba(15,23,42,.97);color:#e2e8f0;box-shadow:0 16px 40px rgba(0,0,0,.28)}
    .refresh-title{font-weight:700;margin-bottom:10px}.refresh-status{margin-top:10px;font-size:.8rem;color:#94a3b8;line-height:1.4}
    .refresh-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}.refresh-grid button{padding:8px 7px;border-radius:8px;border:1px solid rgba(148,163,184,.2);background:#111b2e;color:#e2e8f0;cursor:pointer;font-size:.76rem}.refresh-grid button:hover{border-color:rgba(6,182,212,.55)}
    #refresh-pages{margin-left:8px;border-radius:7px;padding:3px 6px}.refresh-result{margin-top:12px;padding-top:10px;border-top:1px solid rgba(148,163,184,.15);font-size:.78rem;line-height:1.55}.refresh-result .refresh-head{font-weight:700;margin-bottom:5px}.refresh-result .refresh-metrics{display:grid;grid-template-columns:1fr 1fr;gap:4px 10px}.refresh-result .refresh-alert{margin-top:7px;padding:6px 8px;border-radius:7px;background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.18)}
    .refresh-history-title{font-weight:700;margin-top:14px;padding-top:10px;border-top:1px solid rgba(148,163,184,.15)}
    .refresh-history{margin-top:7px;font-size:.72rem;line-height:1.35}.refresh-run{padding:7px 0;border-bottom:1px solid rgba(148,163,184,.10)}.refresh-run:last-child{border-bottom:0}.refresh-run-head{display:flex;justify-content:space-between;gap:8px;font-weight:600}.refresh-run-meta{color:#94a3b8;margin-top:2px}.refresh-run-stats{display:flex;flex-wrap:wrap;gap:4px 10px;margin-top:3px;color:#cbd5e1}.refresh-pill{font-size:.66rem;padding:1px 5px;border-radius:999px;border:1px solid rgba(148,163,184,.16)}
  `;
  document.head.appendChild(style);

  const menu = document.getElementById("refresh-menu");
  const status = document.getElementById("refresh-status");
  const result = document.getElementById("refresh-result");
  const historyBox = document.getElementById("refresh-history");
  document.getElementById("refresh-toggle").addEventListener("click", () => {
    menu.hidden = !menu.hidden;
    if (!menu.hidden) loadHistory();
  });

  function setBusy(message) {
    status.textContent = message;
    panel.querySelectorAll("button[data-apply]").forEach((b) => { b.disabled = true; b.style.opacity = ".55"; });
  }
  function setReady(message) {
    status.textContent = message;
    panel.querySelectorAll("button[data-apply]").forEach((b) => { b.disabled = false; b.style.opacity = "1"; });
  }

  function metricValue(metrics, key) {
    const value = metrics && metrics[key];
    return value === undefined || value === null ? "—" : Number(value).toLocaleString("en-IN");
  }

  function esc(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[c]));
  }

  function renderResult(job, report) {
    if (!job) return;
    const health = job.health || report?.health || {};
    const metrics = job.metrics || {};
    const alerts = job.alerts || report?.alerts || {};
    const healthStatus = health.status || (job.status === "completed" ? "Healthy" : "Failed");
    const score = health.score == null ? "—" : `${health.score}/100`;
    const alertCount = alerts.alert_count ?? alerts.warning_count ?? 0;

    let html = `<div class="refresh-head">${esc(healthStatus)} · Health ${esc(score)}</div>`;
    html += `<div class="refresh-metrics">
      <span>Incoming</span><b>${metricValue(metrics, "incoming_records")}</b>
      <span>Final</span><b>${metricValue(metrics, "final_records")}</b>
      <span>New</span><b>${metricValue(metrics, "new_records")}</b>
      <span>Updated</span><b>${metricValue(metrics, "updated_records")}</b>
      <span>Duplicates</span><b>${metricValue(metrics, "duplicate_records")}</b>
      <span>Invalid</span><b>${metricValue(metrics, "invalid_records")}</b>
      <span>Rating changes</span><b>${metricValue(metrics, "rating_changes")}</b>
      <span>Applied</span><b>${metrics.applied == null ? "—" : String(metrics.applied)}</b>
    </div>`;

    if (alertCount) {
      const items = Array.isArray(alerts.items) ? alerts.items : (Array.isArray(report?.anomalies) ? report.anomalies : []);
      if (items.length) {
        html += `<div class="refresh-alert">${items.slice(0, 3).map(a => `<b>${esc(a.code || a.type || a.severity || "Alert")}</b>: ${esc(a.message || a.reason || "Anomaly detected")}`).join("<br>")}</div>`;
      } else {
        html += `<div class="refresh-alert">${alertCount} alert(s) detected. Check refresh report for details.</div>`;
      }
    }

    if (job.status === "failed") {
      html += `<div class="refresh-alert">Refresh process failed with return code ${job.return_code ?? "?"}.</div>`;
    }
    result.innerHTML = html;
    result.hidden = false;
  }

  function renderHistory(payload) {
    const runs = Array.isArray(payload?.runs) ? payload.runs : [];
    if (!runs.length) {
      historyBox.innerHTML = `<span class="muted">No persisted refresh runs yet.</span>`;
      return;
    }
    const recent = runs.slice(-10).reverse();
    historyBox.innerHTML = recent.map(run => {
      const date = run.snapshot_at ? new Date(run.snapshot_at).toLocaleString() : "Unknown time";
      const mode = Number(run.applied) ? "Apply" : "Dry run";
      const source = run.source || "local";
      const head = `${esc(date)} <span class="refresh-pill">${esc(mode)}</span>`;
      const stats = `New ${metricValue(run, "new_records")} · Updated ${metricValue(run, "updated_records")} · Final ${metricValue(run, "final_records")} · Duplicates ${metricValue(run, "duplicate_records")}`;
      return `<div class="refresh-run"><div class="refresh-run-head"><span>${head}</span><span>${esc(source)}</span></div><div class="refresh-run-stats">${stats}</div><div class="refresh-run-meta">Incoming ${metricValue(run, "incoming_records")} · Invalid ${metricValue(run, "invalid_records")}</div></div>`;
    }).join("");
  }

  async function loadHistory() {
    try {
      const response = await fetch("/api/history", { cache: "no-store" });
      if (!response.ok) return;
      renderHistory(await response.json());
    } catch (_) {
      historyBox.innerHTML = `<span class="muted">Refresh history unavailable.</span>`;
    }
  }

  async function poll() {
    try {
      const response = await fetch("/api/refresh/status", { cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      const job = data.job;
      if (!job) return;
      if (job.status === "running") {
        setBusy(`Running ${job.extended ? "extended" : "core"} refresh · ${job.pages} page(s)…`);
        result.hidden = true;
      } else {
        setReady(`${job.status === "completed" ? "Completed" : "Failed"} · return code ${job.return_code ?? "?"}`);
        renderResult(job, data.report);
        loadHistory();
      }
    } catch (_) {
      // Keep the UI unobtrusive when refresh controls are unavailable.
    }
  }

  panel.querySelectorAll("button[data-apply]").forEach((button) => {
    button.addEventListener("click", async () => {
      const apply = button.dataset.apply === "true";
      const extended = button.dataset.extended === "true";
      if (apply && !window.confirm("Apply this refresh to the master dataset?\n\nA backup is created before the refresh.")) return;
      const pages = Number(document.getElementById("refresh-pages").value || 1);
      const headers = { "Content-Type": "application/json" };
      if (apply) {
        const adminToken = window.prompt("Admin token (required for Apply):", "");
        if (!adminToken) {
          setReady("Apply cancelled: admin token required.");
          return;
        }
        headers["X-Admin-Token"] = adminToken;
      }
      try {
        result.hidden = true;
        setBusy(`Starting ${extended ? "extended" : "core"} ${apply ? "apply" : "dry run"}…`);
        const response = await fetch("/api/refresh", {
          method: "POST",
          headers,
          body: JSON.stringify({ pages, extended, apply })
        });
        const data = await response.json();
        if (!response.ok) {
          setReady(data.error || `Refresh could not start (${response.status}).`);
          return;
        }
        status.textContent = `Started · ${data.job.job_id.slice(0, 8)}`;
        poll();
      } catch (error) {
        setReady("Refresh request failed. Check the Flask console.");
      }
    });
  });

  poll();
  window.setInterval(poll, 2500);
})();
