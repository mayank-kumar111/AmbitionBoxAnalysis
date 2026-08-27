// Dataset health + latest ingestion/change summary for the dashboard.
(function () {
  const $ = (selector) => document.querySelector(selector);

  function formatNumber(value) {
    return Number(value || 0).toLocaleString("en-IN");
  }

  function formatPercent(value) {
    return `${value.toFixed(1)}%`;
  }

  async function loadDataHealth() {
    const status = $("#data-health-status");
    try {
      const response = await fetch("/api/meta");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const meta = await response.json();
      const totals = meta.totals || {};

      const companies = Number(totals.companies || 0);
      const rated = Number(totals.rated || 0);
      const industries = Number(totals.industries || 0);
      const locations = Number(totals.locations || 0);
      const ratingCoverage = companies ? (rated / companies) * 100 : 0;

      const fields = [
        ["data-health-companies", formatNumber(companies)],
        ["data-health-rated", `${formatNumber(rated)} (${formatPercent(ratingCoverage)})`],
        ["data-health-industries", formatNumber(industries)],
        ["data-health-locations", formatNumber(locations)],
      ];

      fields.forEach(([id, value]) => {
        const element = $(`#${id}`);
        if (element) element.textContent = value;
      });

      const updated = $("#data-health-updated");
      if (updated) updated.textContent = "Live from the current application dataset";
      if (status) status.textContent = "Healthy";
    } catch (error) {
      console.error("Unable to load dataset health:", error);
      if (status) status.textContent = "Unavailable";
    }
  }

  function renderRefreshSummary(summary) {
    const status = $("#refresh-summary-status");
    const meta = $("#refresh-summary-meta");
    if (!summary || !summary.available) {
      if (status) status.textContent = "No refresh report";
      if (meta) meta.textContent = "Run the ingestion pipeline to publish the latest change summary.";
      return;
    }

    const values = [
      ["refresh-new", summary.new_records],
      ["refresh-updated", summary.updated_records],
      ["refresh-duplicates", summary.duplicate_records],
      ["refresh-rating", summary.rating_changes],
      ["refresh-invalid", summary.invalid_records],
    ];
    values.forEach(([id, value]) => {
      const element = $(`#${id}`);
      if (element) element.textContent = formatNumber(value);
    });

    if (status) {
      status.textContent = summary.applied ? "Applied" : "Dry run";
    }

    if (meta) {
      const parts = [];
      if (summary.snapshot) parts.push(`Snapshot: ${summary.snapshot}`);
      if (summary.previous_records || summary.incoming_records) {
        parts.push(`Previous: ${formatNumber(summary.previous_records)}`);
        parts.push(`Incoming: ${formatNumber(summary.incoming_records)}`);
      }
      if (summary.collapsed_records) parts.push(`Collapsed duplicates: ${formatNumber(summary.collapsed_records)}`);
      meta.textContent = parts.length ? parts.join(" · ") : "Latest refresh report loaded";
    }
  }

  async function loadRefreshSummary() {
    try {
      let response = await fetch("/static/last_update_report.json", { cache: "no-store" });
      if (!response.ok) {
        response = await fetch("/api/data-quality", { cache: "no-store" });
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      renderRefreshSummary(await response.json());
    } catch (error) {
      console.error("Unable to load refresh summary:", error);
      renderRefreshSummary(null);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadDataHealth();
    loadRefreshSummary();
  });
})();
