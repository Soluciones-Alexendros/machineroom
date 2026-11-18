(function () {
  var form = document.querySelector("[data-search-form]");
  var input = document.querySelector("[data-search]");
  var results = document.querySelector("[data-search-results]");
  if (!input || !results) return;
  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
    });
  }

  var pagefind = null;
  var token = 0;

  function clear() {
    results.hidden = true;
    results.replaceChildren();
  }

  function show(hits) {
    results.replaceChildren();
    if (!hits.length) {
      var empty = document.createElement("p");
      empty.textContent = "No hay resultados.";
      results.append(empty);
      results.hidden = false;
      return;
    }
    var list = document.createElement("ul");
    Promise.all(
      hits.slice(0, 8).map(function (hit) {
        return hit.data().then(function (data) {
          var item = document.createElement("li");
          var link = document.createElement("a");
          link.href = data.url;
          var title = data.meta && data.meta.title;
          link.textContent = title || data.url;
          item.append(link);
          list.append(item);
        });
      })
    ).then(function () {
      results.append(list);
      results.hidden = false;
    });
  }

  input.addEventListener("input", function () {
    var current = ++token;
    var query = input.value.trim();
    if (!query) {
      clear();
      return;
    }
    var loading = pagefind
      ? Promise.resolve(pagefind)
      : import("/pagefind/pagefind.js")
          .then(function (mod) {
            pagefind = mod;
            return mod;
          })
          .catch(function () {
            return null;
          });
    loading
      .then(function (mod) {
        if (!mod || current !== token) return null;
        return mod.search(query);
      })
      .then(function (found) {
        if (!found || current !== token) return;
        show(found.results || []);
      })
      .catch(function () {
        if (current === token) clear();
      });
  });
})();
