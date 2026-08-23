document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("a[href*='pydantic-schemaforms.devsetgo.com']").forEach(function (a) {
    a.setAttribute("target", "_blank");
    a.setAttribute("rel", "noopener noreferrer");
  });
});
