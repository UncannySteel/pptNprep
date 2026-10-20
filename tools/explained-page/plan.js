(function () {
  'use strict';
  var doc = document, root = doc.documentElement;
  function $(s, r) { return (r || doc).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); }

  /* ---------- opening lines: show them, or hide them to test yourself ---------- */
  var pBtns = $$('[data-practice-btn]');
  function setPractice(test) {
    if (test) root.setAttribute('data-practice', ''); else root.removeAttribute('data-practice');
    pBtns.forEach(function (b) { b.setAttribute('aria-pressed', String((b.getAttribute('data-practice-btn') === 'test') === test)); });
    $$('.set.shown').forEach(function (s) { s.classList.remove('shown'); });
    $$('.reveal').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); b.textContent = 'Show the opening line'; });
  }
  pBtns.forEach(function (b) {
    b.addEventListener('click', function () { setPractice(b.getAttribute('data-practice-btn') === 'test'); });
  });
  $$('.reveal').forEach(function (b) {
    b.addEventListener('click', function () {
      var set = b.closest('.set');
      var open = !set.classList.contains('shown');
      set.classList.toggle('shown', open);
      b.setAttribute('aria-expanded', String(open));
      b.textContent = open ? 'Hide it again' : 'Show the opening line';
    });
  });

  /* ---------- every point: filters ---------- */
  var list = $('#pp');
  if (list) {
    var rows = $$('.pp-row', list);
    var chips = $$('#ppTools [data-f]');
    var apply = function () {
      var act = {};
      chips.forEach(function (c) {
        if (c.getAttribute('aria-pressed') === 'true') (act[c.dataset.f] = act[c.dataset.f] || []).push(c.dataset.v);
      });
      var keys = Object.keys(act), shown = 0;
      rows.forEach(function (r) {
        var ok = keys.every(function (f) {
          var have = (r.dataset[f] || '').split(' ');
          return act[f].some(function (v) { return have.indexOf(v) !== -1; });
        });
        r.hidden = !ok;
        if (ok) shown++;
      });
      $('#ppCount').textContent = shown === rows.length ? 'Showing all ' + shown + ' points' : 'Showing ' + shown + ' of ' + rows.length + ' points';
      $('#ppEmpty').hidden = shown !== 0;
      $('#ppClear').hidden = keys.length === 0;
    };
    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        c.setAttribute('aria-pressed', String(c.getAttribute('aria-pressed') !== 'true'));
        apply();
      });
    });
    $('#ppClear').addEventListener('click', function () {
      chips.forEach(function (c) { c.setAttribute('aria-pressed', 'false'); });
      apply();
    });
    apply();
  }

  /* ---------- jump highlight; a filtered-out row is shown again when linked to ---------- */
  function flash(el) {
    el.classList.remove('flash');
    void el.offsetWidth;
    el.classList.add('flash');
    clearTimeout(el._flash);
    el._flash = setTimeout(function () { el.classList.remove('flash'); }, 1900);
  }
  function onHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    var t = doc.getElementById(id);
    if (!t) return;
    if (t.hidden && t.classList.contains('pp-row')) {
      t.hidden = false;
      t.scrollIntoView();
    }
    if (t.matches('.set, .pp-row, .prob, .trap')) flash(t);
  }
  window.addEventListener('hashchange', onHash);
  if (location.hash) setTimeout(onHash, 80);

  /* ---------- back to top ---------- */
  var totop = $('#totop'), ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; totop.hidden = window.scrollY < 900; });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
