(function () {
  var root = document.documentElement;
  var button = document.querySelector("[data-theme-toggle]");
  if (!button) return;

  function prefersDark() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function read() {
    try {
      var stored = localStorage.getItem("theme");
      if (stored === "alexlight" || stored === "alexdark") return stored;
    } catch (err) {
      void err;
    }
    return "system";
  }

  function write(mode) {
    try {
      if (mode === "system") localStorage.removeItem("theme");
      else localStorage.setItem("theme", mode);
    } catch (err) {
      void err;
    }
  }

  function next(mode) {
    if (mode === "system") return prefersDark() ? "alexlight" : "alexdark";
    if (mode === "alexlight") return "alexdark";
    return "system";
  }

  function nameOf(mode) {
    if (mode === "system") return "sistema";
    if (mode === "alexlight") return "claro";
    return "oscuro";
  }

  function apply(mode) {
    if (mode === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", mode);
    var dark = mode === "alexdark" || (mode === "system" && prefersDark());
    root.classList.toggle("cc--darkmode", dark);
    button.setAttribute(
      "aria-label",
      "Tema: " + nameOf(mode) + ". Pulsar para " + nameOf(next(mode))
    );
    button.querySelectorAll("[data-theme-icon]").forEach(function (icon) {
      var match = icon.getAttribute("data-theme-icon") === mode;
      icon.hidden = !match;
      icon.setAttribute("aria-hidden", match ? "false" : "true");
    });
    write(mode);
  }

  var mode = read();
  apply(mode);
  button.addEventListener("click", function () {
    mode = next(mode);
    apply(mode);
  });
})();
