(function() {
  const btn = document.getElementById("theme-toggle");
  if (!btn) return;

  const sun = btn.querySelector(".sun-icon");
  const moon = btn.querySelector(".moon-icon");

  function updateIcons(theme) {
    if (theme === "light") {
      sun.style.display = "block";
      moon.style.display = "none";
    } else {
      sun.style.display = "none";
      moon.style.display = "block";
    }
  }

  // Initial icon setup
  const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
  updateIcons(currentTheme);

  btn.addEventListener("click", () => {
    let theme = document.documentElement.getAttribute("data-theme");
    const newTheme = theme === "light" ? "dark" : "light";
    
    if (newTheme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.removeItem("theme");
    }
    
    updateIcons(newTheme);

    // Dispatch a global event so Chart.js or other elements can redraw dynamically
    window.dispatchEvent(new CustomEvent("themeChanged", { detail: { theme: newTheme } }));
  });
})();
