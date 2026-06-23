document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("img.post-img").forEach(function (img) {
    img.addEventListener("error", function () {
      var url = img.getAttribute("data-original") || img.src;
      var fig = document.createElement("figure");
      fig.className = "missing-image";
      var box = document.createElement("div");
      box.className = "missing-image__box";
      box.textContent = "[ image no longer available ]";
      var cap = document.createElement("figcaption");
      cap.textContent = url;
      fig.appendChild(box);
      fig.appendChild(cap);
      img.replaceWith(fig);
    });
  });
});
