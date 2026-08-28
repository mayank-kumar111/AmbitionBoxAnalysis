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
    </div>`;
  document.body.appendChild(panel);

  const style = document.createElement("style");
  style.textContent = `
    #refresh-control{position:fixed;right:22px;bottom:22px;z-index:9999;font-family:Inter,system-ui,sans-serif}
    #refresh-toggle{border:1px solid rgba(148,163,184,.22);background:rgba(15,23,42,.92);color:#e2e8f0;border-radius:10px;padding:10px 14px;font-weight:700;cursor:pointer;box-shadow:0 8px 28px rgba(0,0,0,.22)}
    #refresh-menu{margin-top:8px;width:285px;padding:14px;border:1px solid rgba(148,163,184,.18);border-radius:12px;background:rgba(15,23,42,.97);color:#e2e8f0;box-shadow:0 16px 40px rgba(0,0,0,.28)}
    .refresh-title{font-weight:700;margin-bottom:10px}.refresh-status{margin-top:10px;font-size:.8rem;color:#94a3b8;line-height:1.4}
    #refresh-pages{margin-left:8px;border-radius:7px;padding:3px 6px}.refresh-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}.refresh-grid button{padding:8px 7px;border-radius:8px;border:1px solid rgba(148,163,184,.2);background:#111b2e;color:#e2e8f0;cursor:pointer;font-size:.76rem}.refresh-grid button:hover{border-color:rgba(6,182,212,.55)}
  `;
  document.head.appendChild(style);

  const menu = document.getElementById("refresh-menu");
  const status = document.getElementById("refresh-status");
  document.getElementById("refresh-toggle").addEventListener("click", () => {
    menu.hidden = !menu.hidden;
  });

  function setBusy(message) {
    status.textContent = message;
    panel.querySelectorAll("button[data-apply]").forEach((b) => { b.disabled = true; b.style.opacity = ".55"; });
  }
  function setReady(message) {
    status.textContent = message;
    panel.querySelectorAll("button[data-apply]").forEach((b) => { b.disabled = false; b.style.opacity = "1"; });
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
      } else {
        setReady(`${job.status === "completed" ? "Completed" : "Failed"} · return code ${job.return_code ?? "?"}`);
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
      try {
        setBusy(`Starting ${extended ? "extended" : "core"} ${apply ? "apply" : "dry run"}…`);
        const response = await fetch("/api/refresh", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
