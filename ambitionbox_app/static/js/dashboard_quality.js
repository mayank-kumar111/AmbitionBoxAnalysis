// Dataset health and coverage cards for the dashboard.
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
      if (updated) {
        updated.textContent = "Live from the current application dataset";
      }
      if (status) status.textContent = "Healthy";
    } catch (error) {
      console.error("Unable to load dataset health:", error);
      if (status) status.textContent = "Unavailable";
    }
  }

  document.addEventListener("DOMContentLoaded", loadDataHealth);
})();
