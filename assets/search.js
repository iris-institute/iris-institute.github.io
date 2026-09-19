(function () {
  'use strict';

  var STRINGS = {
    ja: { placeholder: '書籍・テーマを検索', empty: '見つかりませんでした', book: '書籍', series: 'シリーズ', library: 'ライブラリ', page: 'ページ' },
    en: { placeholder: 'Search books & topics', empty: 'No results found', book: 'Book', series: 'Series', library: 'Library', page: 'Page' },
    es: { placeholder: 'Buscar libros y temas', empty: 'No se encontraron resultados', book: 'Libro', series: 'Serie', library: 'Biblioteca', page: 'Página' },
    de: { placeholder: 'Bücher & Themen suchen', empty: 'Keine Ergebnisse gefunden', book: 'Buch', series: 'Serie', library: 'Bibliothek', page: 'Seite' },
    fr: { placeholder: 'Rechercher livres et thèmes', empty: 'Aucun résultat trouvé', book: 'Livre', series: 'Série', library: 'Bibliothèque', page: 'Page' }
  };

  function init() {
    var widget = document.querySelector('.search-widget');
    if (!widget) return;

    var lang = (document.documentElement.lang || 'ja').split('-')[0];
    var t = STRINGS[lang] || STRINGS.ja;

    var toggle = widget.querySelector('.search-toggle');
    var panel = widget.querySelector('.search-panel');
    var input = widget.querySelector('.search-input');
    var results = widget.querySelector('.search-results');

    input.placeholder = t.placeholder;

    var indexData = null;
    var indexPromise = null;

    function loadIndex() {
      if (!indexPromise) {
        indexPromise = fetch('/assets/search-index.json')
          .then(function (res) { return res.json(); })
          .then(function (data) { indexData = data; return data; })
          .catch(function () { indexData = []; return []; });
      }
      return indexPromise;
    }

    function open() {
      widget.classList.add('search-open');
      toggle.setAttribute('aria-expanded', 'true');
      loadIndex();
      input.focus();
    }

    function close() {
      widget.classList.remove('search-open');
      toggle.setAttribute('aria-expanded', 'false');
    }

    function score(entry, q) {
      var title = entry.t.toLowerCase();
      if (title === q) return 100;
      if (title.indexOf(q) === 0) return 80;
      if (title.indexOf(q) !== -1) return 60;
      if (entry.h && entry.h.toLowerCase().indexOf(q) !== -1) return 30;
      return 0;
    }

    function render(query) {
      var q = query.trim().toLowerCase();
      if (!q) { results.innerHTML = ''; results.hidden = true; return; }
      var data = indexData || [];
      var scored = [];
      for (var i = 0; i < data.length; i++) {
        var s = score(data[i], q);
        if (s > 0) scored.push({ e: data[i], s: s });
      }
      scored.sort(function (a, b) { return b.s - a.s; });
      scored = scored.slice(0, 8);

      results.hidden = false;
      if (scored.length === 0) {
        results.innerHTML = '<div class="search-empty">' + t.empty + '</div>';
        return;
      }
      var html = '';
      for (var j = 0; j < scored.length; j++) {
        var entry = scored[j].e;
        var typeLabel = t[entry.y] || entry.y;
        html += '<a class="search-result" href="' + entry.u + '">' +
          '<span class="search-result-title">' + escapeHtml(entry.t) + '</span>' +
          '<span class="search-result-type">' + typeLabel + '</span>' +
          '</a>';
      }
      results.innerHTML = html;
    }

    function escapeHtml(s) {
      var div = document.createElement('div');
      div.textContent = s;
      return div.innerHTML;
    }

    toggle.addEventListener('click', function () {
      if (widget.classList.contains('search-open')) {
        close();
      } else {
        open();
      }
    });

    input.addEventListener('input', function () {
      if (indexData) {
        render(input.value);
      } else {
        loadIndex().then(function () { render(input.value); });
      }
    });

    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && widget.classList.contains('search-open')) {
        close();
        toggle.focus();
      }
    });

    document.addEventListener('click', function (ev) {
      if (!widget.contains(ev.target)) close();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
