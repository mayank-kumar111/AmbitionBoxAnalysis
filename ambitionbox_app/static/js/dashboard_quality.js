// Dataset health + latest ingestion/change summary + anomaly alerts.
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

      [
        ["data-health-companies", formatNumber(companies)],
        ["data-health-rated", `${formatNumber(rated)} (${formatPercent(ratingCoverage)})`],
        ["data-health-industries", formatNumber(industries)],
        ["data-health-locations", formatNumber(locations)],
      ].forEach(([id, value]) => {
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

  function renderAnomalies(summary) {
    const box = $("#refresh-anomalies");
    if (!box) return;
    const anomalies = Array.isArray(summary && summary.anomalies) ? summary.anomalies : [];
    if (!anomalies.length) {
      box.innerHTML = '<div class="sub">No anomalies detected in the latest run.</div>';
      return;
    }
    box.innerHTML = anomalies.map(item => {
      const severity = String(item.severity || "warning").toLowerCase();
      return `<div class="data-anomaly data-anomaly-${severity}">
        <div><b>${severity.toUpperCase()}: ${String(item.code || "ANOMALY")}</b></div>
        <div class="sub">${String(item.message || "Suspicious refresh condition detected.")}</div>
      </div>`;
    }).join("");
  }

  function renderRefreshSummary(summary) {
    const status = $("#refresh-summary-status");
    const meta = $("#refresh-summary-meta");
    if (!summary || !summary.available) {
      if (status) status.textContent = "No refresh report";
      if (meta) meta.textContent = "Run the ingestion pipeline to publish the latest change summary.";
      renderAnomalies({ anomalies: [] });
      return;
    }

    [
      ["refresh-new", summary.new_records],
      ["refresh-updated", summary.updated_records],
      ["refresh-duplicates", summary.duplicate_records],
      ["refresh-rating", summary.rating_changes],
      ["refresh-invalid", summary.invalid_records],
    ].forEach(([id, value]) => {
      const element = $(`#${id}`);
      if (element) element.textContent = formatNumber(value);
    });

    if (status) {
      if (summary.critical_anomalies && summary.critical_anomalies.length) status.textContent = "Blocked by anomaly";
      else if (summary.anomalies_found) status.textContent = summary.applied ? "Applied with warnings" : "Warnings detected";
      else status.textContent = summary.applied ? "Applied" : "Dry run";
    }

    if (meta) {
      const parts = [];
      if (summary.snapshot) parts.push(`Snapshot: ${summary.snapshot}`);
      if (summary.previous_records || summary.incoming_records) {
        parts.push(`Previous: ${formatNumber(summary.previous_records)}`);
        parts.push(`Incoming: ${formatNumber(summary.incoming_records)}`);
      }
      if (summary.collapsed_records) parts.push(`Collapsed duplicates: ${formatNumber(summary.collapsed_records)}`);
      if (summary.critical_anomalies && summary.critical_anomalies.length) {
        parts.push(`Critical anomalies: ${formatNumber(summary.critical_anomalies.length)}`);
      }
      meta.textContent = parts.length ? parts.join(" · ") : "Latest refresh report loaded";
    }
    renderAnomalies(summary);
  }

  async function loadRefreshSummary() {
    try {
      const response = await fetch("/static/last_update_report.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const report = await response.json();
      report.available = true;
      renderRefreshSummary(report);
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
