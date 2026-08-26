// Click-to-copy helper with a small toast confirmation.
(function () {
  const toast = document.createElement("div");
  toast.className = "toast";
  document.body.appendChild(toast);
  let timer;
  function showToast(msg) {
    toast.innerHTML = '<span class="ok"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></span>' + msg;
    toast.classList.add("show");
    clearTimeout(timer);
    timer = setTimeout(() => toast.classList.remove("show"), 1900);
  }
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const val = btn.getAttribute("data-copy");
      try {
        await navigator.clipboard.writeText(val);
      } catch (_) {
        const t = document.createElement("textarea");
        t.value = val; document.body.appendChild(t); t.select();
        try { document.execCommand("copy"); } catch (e) {}
        t.remove();
      }
      showToast("Copied &nbsp;·&nbsp; " + val);
    });
  });
})();
