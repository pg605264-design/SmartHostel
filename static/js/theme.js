/**
 * SmartHostel — Theme System (Light / Dark / System)
 * Persists choice in localStorage and respects OS system preferences.
 */
(function () {
  const STORAGE_KEY = "smarthostel-theme-mode";
  const root = document.documentElement;

  function getSystemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function resolveTheme(preference) {
    if (preference === "system") {
      return getSystemTheme();
    }
    return preference === "dark" ? "dark" : "light";
  }

  function updateIconAndMenu(preference, resolvedTheme) {
    // Update topbar trigger icon
    const themeIcons = document.querySelectorAll(".theme-trigger-icon");
    themeIcons.forEach((icon) => {
      if (preference === "system") {
        icon.className = "fa-solid fa-desktop theme-trigger-icon";
      } else if (preference === "dark") {
        icon.className = "fa-solid fa-moon theme-trigger-icon";
      } else {
        icon.className = "fa-solid fa-sun theme-trigger-icon";
      }
    });

    // Update active state in theme menu options
    const options = document.querySelectorAll(".theme-option");
    options.forEach((opt) => {
      const mode = opt.getAttribute("data-theme-value");
      if (mode === preference) {
        opt.classList.add("active");
        opt.setAttribute("aria-selected", "true");
      } else {
        opt.classList.remove("active");
        opt.setAttribute("aria-selected", "false");
      }
    });
  }

  function applyTheme(preference) {
    const resolved = resolveTheme(preference);
    root.setAttribute("data-theme", resolved);
    localStorage.setItem(STORAGE_KEY, preference);
    updateIconAndMenu(preference, resolved);
  }

  // Load saved preference or default to 'system'
  const savedPreference = localStorage.getItem(STORAGE_KEY) || "system";
  applyTheme(savedPreference);

  // Listen for OS system theme changes if set to 'system'
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    const currentPref = localStorage.getItem(STORAGE_KEY) || "system";
    if (currentPref === "system") {
      applyTheme("system");
    }
  });

  // Global event delegation
  document.addEventListener("DOMContentLoaded", () => {
    applyTheme(localStorage.getItem(STORAGE_KEY) || "system");
  });

  document.addEventListener("click", (e) => {
    // Click on theme option
    const optionBtn = e.target.closest(".theme-option");
    if (optionBtn) {
      const val = optionBtn.getAttribute("data-theme-value");
      if (val) {
        applyTheme(val);
        document.getElementById("themePopover")?.classList.remove("open");
      }
      return;
    }

    // Toggle theme popover menu
    const themeBtn = e.target.closest("#themeToggleBtn");
    if (themeBtn) {
      e.stopPropagation();
      document.getElementById("themePopover")?.classList.toggle("open");
      document.getElementById("notifDropdown")?.classList.remove("open");
      return;
    }

    // Sidebar toggle for mobile drawer
    if (e.target.closest("#sidebarToggle")) {
      document.getElementById("sidebar")?.classList.toggle("open");
      document.getElementById("sidebarOverlay")?.classList.toggle("open");
      return;
    }

    // Sidebar overlay click to close
    if (e.target.closest("#sidebarOverlay")) {
      document.getElementById("sidebar")?.classList.remove("open");
      document.getElementById("sidebarOverlay")?.classList.remove("open");
      return;
    }

    // Close theme popover if clicked outside
    const popover = document.getElementById("themePopover");
    if (popover && popover.classList.contains("open")) {
      if (!e.target.closest(".theme-switcher-wrapper")) {
        popover.classList.remove("open");
      }
    }
  });

  // Keyboard navigation (ESC key)
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.getElementById("themePopover")?.classList.remove("open");
      document.getElementById("sidebar")?.classList.remove("open");
      document.getElementById("sidebarOverlay")?.classList.remove("open");
    }
  });
})();
