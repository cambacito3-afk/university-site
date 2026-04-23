document.addEventListener("DOMContentLoaded", function () {
  var navbars = document.querySelectorAll(".navbar");

  navbars.forEach(function (navbar, index) {
    var toggle = navbar.querySelector(".nav-toggle");
    var menu = navbar.querySelector(".nav-links");

    if (!toggle || !menu) {
      return;
    }

    if (!menu.id) {
      menu.id = "main-menu-" + index;
    }

    toggle.setAttribute("aria-controls", menu.id);

    function closeMenu() {
      navbar.classList.remove("menu-visible");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Open main menu");
      document.body.classList.remove("menu-open");
    }

    function openMenu() {
      navbar.classList.add("menu-visible");
      toggle.setAttribute("aria-expanded", "true");
      toggle.setAttribute("aria-label", "Close main menu");
      document.body.classList.add("menu-open");
    }

    toggle.addEventListener("click", function () {
      var expanded = toggle.getAttribute("aria-expanded") === "true";

      if (expanded) {
        closeMenu();
        return;
      }

      openMenu();
    });

    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeMenu);
    });

    document.addEventListener("click", function (event) {
      if (!navbar.contains(event.target)) {
        closeMenu();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeMenu();
      }
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 860) {
        closeMenu();
      }
    });
  });
});
