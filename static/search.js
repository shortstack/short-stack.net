(function () {
  var input = document.getElementById("q");
  var results = document.getElementById("results");
  if (!input || !results) return;

  var index = [];
  var ready = false;
  fetch("/search-index.json")
    .then(function (r) { return r.json(); })
    .then(function (data) { index = data; ready = true; render(input.value); });

  function render(q) {
    q = (q || "").trim().toLowerCase();
    results.innerHTML = "";
    if (!ready || q.length < 2) return;
    var terms = q.split(/\s+/);
    var hits = index.filter(function (p) {
      var hay = (p.title + " " + (p.text || "")).toLowerCase();
      return terms.every(function (t) { return hay.indexOf(t) !== -1; });
    }).slice(0, 100);
    hits.forEach(function (p) {
      var li = document.createElement("li");
      li.className = "post-item";
      var a = document.createElement("a");
      a.className = "post-link";
      a.href = p.url;
      a.textContent = p.title;
      var t = document.createElement("time");
      t.textContent = p.date;
      li.appendChild(a);
      li.appendChild(t);
      results.appendChild(li);
    });
    if (!hits.length) {
      var li = document.createElement("li");
      li.className = "post-item";
      li.textContent = "no matches";
      results.appendChild(li);
    }
  }

  var timer;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { render(input.value); }, 120);
  });
}());
