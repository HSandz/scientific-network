(function () {
  try {
    var saved =
      window.localStorage.getItem("scientific-network-theme-v1") ||
      window.localStorage.getItem("scientific-network-theme");
    if (saved === "light") {
      document.documentElement.classList.remove("dark");
    } else {
      document.documentElement.classList.add("dark");
    }
  } catch (_err) {
    document.documentElement.classList.add("dark");
  }
})();

