(function () {
  const $ = (s) => document.querySelector(s);
  let chart = null;

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    }[c]));
  }

  function showError(message) {
    const box = $("#company-error");
    box.textContent = message;
    box.style.display = "block";
    $("#company-profile").style.display = "none";
  }

  function render(data) {
    $("#company-error").style.display = "none";
    $("#company-profile").style.display = "block";

    const c = data.company;
    $("#company-title").textContent = c.company_name;
    $("#company-subtitle").textContent = [c.industry, c.location].filter(Boolean).join(" · ");
    $("#company-current-rating").textContent = c.company_rating ?? "—";
    $("#company-rating-change").textContent = data.rating_change == null ? "—" : `${data.rating_change >= 0 ? "+" : ""}${data.rating_change.toFixed(2)}`;
    $("#company-first-seen").textContent = c.first_seen || "—";
    $("#company-last-seen").textContent = c.last_seen || "—";

    $("#company-details").innerHTML = [
      ["Industry", c.industry], ["Size", c.size], ["Type", c.type],
      ["Age", c.years_old == null ? null : `${c.years_old} years`],
      ["Locations", data.locations.join(", ")]
    ].map(([label, value]) => `<div><b>${escapeHtml(label)}:</b> ${escapeHtml(value || "—")}</div>`).join("");

    const rows = data.changes;
    $("#company-changes").innerHTML = rows.length
      ? `<table class="data-table"><thead><tr><th>Date</th><th>Type</th><th>Field</th><th>Old</th><th>New</th></tr></thead><tbody>${rows.map(r => `<tr><td>${escapeHtml(r.snapshot_at)}</td><td>${escapeHtml(r.change_type)}</td><td>${escapeHtml(r.field_name || "—")}</td><td>${escapeHtml(r.old_value || "—")}</td><td>${escapeHtml(r.new_value || "—")}</td></tr>`).join("")}</tbody></table>`
      : '<p class="muted">No field-level changes recorded for this company.</p>';

    const ctx = $("#company-rating-chart");
    if (chart) chart.destroy();
    if (ctx && data.snapshots.length && typeof Chart !== "undefined") {
      chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: data.snapshots.map(s => s.snapshot_at),
          datasets: [{
            label: "Rating",
            data: data.snapshots.map(s => s.company_rating),
            tension: 0.25,
            spanGaps: true,
            fill: true
          }]
        },
        options: {
          maintainAspectRatio: false,
          scales: { y: { min: 1, max: 5 } },
          plugins: { legend: { display: false } }
        }
      });
    }
  }

  async function load() {
    const name = $("#company-name-input").value.trim();
    const location = $("#company-location-input").value.trim();
    if (!name) return;

    try {
      const params = new URLSearchParams({ name });
      if (location) params.set("location", location);
      const response = await fetch(`/api/history/company?${params}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      render(data);
      history.replaceState(null, "", `/history/company?${params}`);
    } catch (error) {
      console.error("Company history load failed:", error);
      showError(error.message || "Unable to load company history.");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    $("#company-history-form").addEventListener("submit", (event) => {
      event.preventDefault();
      load();
    });
    if ($( "#company-name-input").value.trim()) load();
  });
})();
