(function () {
  const STORAGE_KEY = "bc-theme";
  let mobileMenuCounter = 0;

  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function getInitialTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") {
      return saved;
    }
    return systemPrefersDark() ? "dark" : "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    const button = document.getElementById("theme-toggle");
    if (button) {
      button.setAttribute("aria-label", theme === "dark" ? "Включить светлую тему" : "Включить темную тему");
      button.textContent = theme === "dark" ? "☀" : "◐";
    }
  }

  function mountToggle() {
    if (document.getElementById("theme-toggle")) {
      return;
    }
    const button = document.createElement("button");
    button.id = "theme-toggle";
    button.type = "button";
    button.className = "theme-toggle";
    button.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      applyTheme(current === "dark" ? "light" : "dark");
    });
    document.body.appendChild(button);
    applyTheme(document.documentElement.getAttribute("data-theme") || getInitialTheme());
  }

  function closeAllMobileMenus(exceptId) {
    document.querySelectorAll("[data-mobile-menu]").forEach((menu) => {
      if (exceptId && menu.dataset.mobileMenuId === exceptId) {
        return;
      }
      menu.classList.remove("is-open");
      if (menu.id) {
        const toggle = document.querySelector(`.mobile-menu-toggle[aria-controls="${menu.id}"]`);
        if (toggle) {
          toggle.setAttribute("aria-expanded", "false");
        }
      }
    });
  }

  function mountMobileMenus() {
    const menus = Array.from(document.querySelectorAll("[data-mobile-menu]"));
    menus.forEach((menu) => {
      const host = menu.parentElement;
      if (!host || host.querySelector(".mobile-menu-toggle")) {
        return;
      }
      host.classList.add("mobile-menu-host");
      mobileMenuCounter += 1;
      const menuId = `mobile-menu-${mobileMenuCounter}`;
      menu.dataset.mobileMenuId = menuId;

      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "mobile-menu-toggle";
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-controls", menuId);
      toggle.textContent = "≡";
      menu.id = menuId;

      toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        const isOpen = menu.classList.contains("is-open");
        closeAllMobileMenus(isOpen ? undefined : menuId);
        menu.classList.toggle("is-open", !isOpen);
        toggle.setAttribute("aria-expanded", String(!isOpen));
      });

      menu.addEventListener("click", (event) => {
        event.stopPropagation();
      });

      host.insertBefore(toggle, menu);
    });

    document.addEventListener("click", () => {
      closeAllMobileMenus();
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth >= 700) {
        closeAllMobileMenus();
      }
    });
  }

  document.documentElement.setAttribute("data-theme", getInitialTheme());

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      mountToggle();
      mountMobileMenus();
    });
  } else {
    mountToggle();
    mountMobileMenus();
  }
})();
