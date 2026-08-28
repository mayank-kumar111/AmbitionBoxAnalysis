// Lightweight dataset freshness indicator.
(function () {
  const POLL_MS = 30000;

  function ensureBadge() {
    let badge = document.getElementById("dataset-status-runtime");
    if (badge) return badge;

    const header = document.querySelector(".nav");
    if (!header) return null;

    badge = document.createElement("span");
    badge.id = "dataset-status-runtime";
    badge.title = "Current dataset status";
    badge.style.cssText = [
      "display:flex", "align-items:center", "gap:6px", "font-size:.78rem",
      "color:var(--text-dim)", "white-space:nowrap", "margin-left:auto"
    ].join(";");

    const dot = document.createElement("span");
    dot.id = "dataset-status-dot";
    dot.style.cssText = "width:7px;height:7px;border-radius:50%;background:currentColor;display:inline-block;";

    const text = document.createElement("span");
    text.id = "dataset-status-text";
    text.textContent = "Dataset status…";

    badge.append(dot, text);
    const target = header.querySelector(".global-search") || header.lastElementChild;
    if (target) header.insertBefore(badge, target);
    return badge;
  }

  function render(data) {
    const badge = ensureBadge();
    if (!badge) return;
    const dot = badge.querySelector("#dataset-status-dot");
    const text = badge.querySelector("#dataset-status-text");
    const count = Number(data.data_records || 0).toLocaleString("en-IN");
    const status = data.status || "unknown";

    text.textContent = `${count} companies`;
    badge.title = `Dataset: ${count} companies · ${status}`;
    if (status === "ok") {
      dot.style.opacity = "1";
    } else {
      dot.style.opacity = ".45";
    }
  }

  async function load() {
    try {
      const response = await fetch("/health", { cache: "no-store" });
      if (!response.ok) throw new Error(`health ${response.status}`);
      render(await response.json());
    } catch (error) {
      const badge = ensureBadge();
      const text = badge && badge.querySelector("#dataset-status-text");
      if (text) text.textContent = "Dataset unavailable";
      console.warn("Dataset status check failed:", error);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    load();
    window.setInterval(load, POLL_MS);
  });
})();
