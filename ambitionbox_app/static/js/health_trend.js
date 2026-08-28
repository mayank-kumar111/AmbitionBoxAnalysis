(function () {
  function number(value) { return Number(value || 0).toLocaleString("en-IN"); }

  async function loadHealthTrend() {
    const score = document.getElementById("health-latest-score");
    const status = document.getElementById("health-latest-status");
    const average = document.getElementById("health-average-score");
    const blocked = document.getElementById("health-blocked-runs");
    const canvas = document.getElementById("health-trend");
    if (!score && !status && !canvas) return;

    try {
      const response = await fetch("/static/refresh_health_history.json", { cache: "no-store" });
      if (!response.ok) return;
      const runs = await response.json();
      if (!Array.isArray(runs) || !runs.length) return;

      const scores = runs.map(r => Number(r.health_score)).filter(Number.isFinite);
      const latest = runs[runs.length - 1];
      const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null;
      const blockedCount = runs.filter(r => String(r.health_status).toLowerCase() === "blocked").length;

      if (score) score.textContent = latest.health_score == null ? "—" : `${latest.health_score}/100`;
      if (status) status.textContent = String(latest.health_status || "unknown").replace(/^./, c => c.toUpperCase());
      if (average) average.textContent = avg == null ? "—" : `${avg.toFixed(1)}/100`;
      if (blocked) blocked.textContent = number(blockedCount);

      if (canvas && typeof Chart !== "undefined") {
        new Chart(canvas, {
          type: "line",
          data: { labels: runs.map(r => r.snapshot), datasets: [{ label: "Health score", data: runs.map(r => r.health_score), tension: 0.3, fill: true }] },
          options: { maintainAspectRatio: false, scales: { y: { min: 0, max: 100 } }, plugins: { legend: { display: false } } }
        });
      }
    } catch (error) {
      console.error("Unable to load health trend:", error);
    }
  }

  document.addEventListener("DOMContentLoaded", loadHealthTrend);
})();
