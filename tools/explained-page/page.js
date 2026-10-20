(function () {
  'use strict';
  var doc = document, root = doc.documentElement;
  function $(s, r) { return (r || doc).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || doc).querySelectorAll(s)); }
  var store = {
    get: function (k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* storage blocked: the page still works */ } }
  };
  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  }
  function squash(s) { return s.replace(/\s+/g, ' ').trim(); }
  // Case- and punctuation-folding that keeps every character in place, so match
  // positions found in the folded text also apply to the original text.
  function fold(s) {
    return s.toLowerCase()
      .replace(/[‘’]/g, "'")
      .replace(/[“”]/g, '"')
      .replace(/[‐-―−]/g, '-');
  }

  /* ---------- how much of each entry to show ---------- */
  var viewBtns = $$('[data-view-btn]');
  function firstVisiblePoint() {
    var top = $('.bar').getBoundingClientRect().bottom;
    var pts = $$('.pt');
    for (var i = 0; i < pts.length; i++) { if (pts[i].getBoundingClientRect().bottom > top + 8) return pts[i]; }
    return null;
  }
  function setView(v, keepPlace) {
    var anchor = keepPlace ? firstVisiblePoint() : null;
    var before = anchor ? anchor.getBoundingClientRect().top : 0;
    if (v === 'actions') root.setAttribute('data-view', 'actions'); else root.removeAttribute('data-view');
    viewBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-view-btn') === v)); });
    $$('.pt.show-all').forEach(function (a) { a.classList.remove('show-all'); });
    $$('.pt-more').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); b.textContent = 'Show the full explanation'; });
    store.set('abotrt.view', v);
    if (anchor) window.scrollBy({ top: anchor.getBoundingClientRect().top - before, behavior: 'instant' });
  }
  viewBtns.forEach(function (b) {
    b.addEventListener('click', function () { setView(b.getAttribute('data-view-btn'), true); });
  });
  setView(store.get('abotrt.view') === 'actions' ? 'actions' : 'full', false);
  $$('.pt-more').forEach(function (b) {
    b.addEventListener('click', function () {
      var pt = b.closest('.pt');
      var open = !pt.classList.contains('show-all');
      pt.classList.toggle('show-all', open);
      b.setAttribute('aria-expanded', String(open));
      b.textContent = open ? 'Hide the full explanation' : 'Show the full explanation';
    });
  });

  /* ---------- contents drawer (phones and tablets) ---------- */
  var menuBtn = $('#menuBtn'), toc = $('#toc'), scrim = $('#scrim');
  var narrow = window.matchMedia('(max-width: 63.99rem)');
  function openToc(open) {
    root.classList.toggle('toc-open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
    scrim.hidden = !open;
    if (open) {
      var cur = $('a[aria-current="location"]', toc) || $('a', toc);
      setTimeout(function () { cur.focus(); }, 40);
    }
  }
  menuBtn.addEventListener('click', function () { openToc(menuBtn.getAttribute('aria-expanded') !== 'true'); });
  $('#tocClose').addEventListener('click', function () { openToc(false); menuBtn.focus(); });
  scrim.addEventListener('click', function () { openToc(false); });
  toc.addEventListener('click', function (e) { if (e.target.closest('a') && narrow.matches) openToc(false); });
  if (narrow.addEventListener) narrow.addEventListener('change', function () { if (!narrow.matches) openToc(false); });

  /* ---------- where am I: highlight the contents entry for the current section ---------- */
  var tocLinks = $$('#toc a[href^="#"]');
  var targets = tocLinks.map(function (a) { return doc.getElementById(a.getAttribute('href').slice(1)); });
  var totop = $('#totop');
  function spy() {
    var line = $('.bar').getBoundingClientRect().bottom + 40;
    var current = -1;
    for (var i = 0; i < targets.length; i++) {
      if (targets[i] && targets[i].getBoundingClientRect().top <= line) current = i;
    }
    tocLinks.forEach(function (a) { a.removeAttribute('aria-current'); a.classList.remove('is-current'); });
    if (current < 0) return;
    var a = tocLinks[current];
    a.setAttribute('aria-current', 'location');
    var sub = a.closest('ol.sub');
    if (sub) { var parent = sub.parentElement.querySelector('a'); if (parent) parent.classList.add('is-current'); }
    if (!narrow.matches && toc.scrollHeight > toc.clientHeight) {
      var y = a.offsetTop;
      if (y < toc.scrollTop + 40 || y > toc.scrollTop + toc.clientHeight - 60) toc.scrollTop = y - toc.clientHeight / 3;
    }
  }
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      spy();
      totop.hidden = window.scrollY < 900;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  onScroll();

  /* ---------- jump highlight ---------- */
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
    if (t && t.matches('.pt, .q, .rule, .grp, .ck li, .gloss div')) flash(t);
  }
  window.addEventListener('hashchange', onHash);
  if (location.hash) setTimeout(onHash, 80);

  /* ---------- the 52-point index: filters and sorting ---------- */
  var idx = $('#idx');
  if (idx) {
    var rows = $$('tbody tr', idx);
    var chips = $$('#idxTools [data-f]');
    var applyIdx = function () {
      var act = {};
      chips.forEach(function (c) {
        if (c.getAttribute('aria-pressed') === 'true') (act[c.dataset.f] = act[c.dataset.f] || []).push(c.dataset.v);
      });
      var keys = Object.keys(act), shown = 0;
      rows.forEach(function (r) {
        var ok = keys.every(function (f) { return act[f].indexOf(r.dataset[f]) !== -1; });
        r.hidden = !ok;
        if (ok) shown++;
      });
      $('#idxCount').textContent = shown === rows.length ? 'Showing all ' + shown + ' points' : 'Showing ' + shown + ' of ' + rows.length + ' points';
      $('#idxEmpty').hidden = shown !== 0;
      $('#idxClear').hidden = keys.length === 0;
    };
    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        c.setAttribute('aria-pressed', String(c.getAttribute('aria-pressed') !== 'true'));
        applyIdx();
      });
    });
    $('#idxClear').addEventListener('click', function () {
      chips.forEach(function (c) { c.setAttribute('aria-pressed', 'false'); });
      applyIdx();
    });
    var sortBtns = $$('#idxTools [data-sort]');
    sortBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        var byScore = b.dataset.sort === 'score', body = $('tbody', idx);
        rows.slice().sort(function (x, y) {
          if (byScore) { var d = Number(y.dataset.score) - Number(x.dataset.score); if (d) return d; }
          return x.id < y.id ? -1 : 1;
        }).forEach(function (r) { body.appendChild(r); });
        sortBtns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
      });
    });
    applyIdx();
  }

  /* ---------- search ---------- */
  var q = $('#q'), panel = $('#results'), index = null, tokens = [];
  var KINDS = [
    ['Questions', 'Questions to prepare for', 8],
    ['Rules', 'Wording rules', 8],
    ['Points', 'Points', 30],
    ['Groups', 'Set-aside groups', 8],
    ['Checklist', 'Slide checklist', 8],
    ['Glossary', 'Glossary', 10],
    ['Sections', 'Other sections', 4]
  ];
  function buildIndex() {
    index = $$('[data-search]').map(function (el, order) {
      var text = squash(el.textContent);
      var title = el.getAttribute('data-title') || '';
      var key = el.getAttribute('data-key') || '';
      return {
        kind: el.getAttribute('data-search'), href: el.getAttribute('data-href'), key: key,
        title: title, text: text, ft: fold(text), fh: fold(key + ' ' + title), order: order
      };
    });
  }
  function find(query) {
    if (!index) buildIndex();
    tokens = fold(squash(query)).split(' ').filter(Boolean);
    var hits = [];
    index.forEach(function (e) {
      for (var i = 0; i < tokens.length; i++) {
        if (e.ft.indexOf(tokens[i]) === -1 && e.fh.indexOf(tokens[i]) === -1) return;
      }
      var score = 0;
      tokens.forEach(function (t) {
        if (e.fh.indexOf(t) !== -1) score += 6;
        score += Math.min(e.ft.split(t).length - 1, 5);
      });
      hits.push({ e: e, score: score });
    });
    return hits;
  }
  function markText(s) {
    var f = fold(s), ranges = [];
    tokens.forEach(function (t) {
      var i = f.indexOf(t);
      while (i !== -1) { ranges.push([i, i + t.length]); i = f.indexOf(t, i + t.length); }
    });
    if (!ranges.length) return esc(s);
    ranges.sort(function (a, b) { return a[0] - b[0]; });
    var merged = [ranges[0]];
    for (var k = 1; k < ranges.length; k++) {
      var last = merged[merged.length - 1];
      if (ranges[k][0] <= last[1]) last[1] = Math.max(last[1], ranges[k][1]); else merged.push(ranges[k]);
    }
    var out = '', p = 0;
    merged.forEach(function (r) { out += esc(s.slice(p, r[0])) + '<mark>' + esc(s.slice(r[0], r[1])) + '</mark>'; p = r[1]; });
    return out + esc(s.slice(p));
  }
  function snippet(e) {
    var pos = -1, len = 0;
    tokens.forEach(function (t) {
      var p = e.ft.indexOf(t);
      if (p !== -1 && (pos === -1 || p < pos)) { pos = p; len = t.length; }
    });
    var s = e.text;
    if (pos === -1) return markText(s.slice(0, 140)) + (s.length > 140 ? '…' : '');
    var start = Math.max(0, pos - 55), end = Math.min(s.length, pos + len + 95);
    if (start > 0) { var a = s.indexOf(' ', start); if (a !== -1 && a < pos) start = a + 1; }
    if (end < s.length) { var b = s.lastIndexOf(' ', end); if (b > pos + len) end = b; }
    return (start > 0 ? '…' : '') + markText(s.slice(start, end)) + (end < s.length ? '…' : '');
  }
  function render(hits, query) {
    var out = [];
    if (!hits.length) {
      out.push('<p class="res-none">Nothing matches “' + esc(query) + '”. Try one word, a number such as 4.7, or an ID such as P-20.</p>');
    } else {
      out.push('<p class="res-count">' + hits.length + (hits.length === 1 ? ' match' : ' matches') + '</p>');
    }
    KINDS.forEach(function (k) {
      var group = hits.filter(function (h) { return h.e.kind === k[0]; });
      if (!group.length) return;
      group.sort(function (x, y) { return (y.score - x.score) || (x.e.order - y.e.order); });
      out.push('<p class="res-g lbl">' + k[1] + ' <span>' + group.length + '</span></p>');
      group.slice(0, k[2]).forEach(function (h) {
        var e = h.e;
        out.push('<a class="res" href="' + esc(e.href) + '"><span class="res-k">' + esc(e.key) + '</span>' +
          '<span class="res-t">' + markText(e.title) + '</span><span class="res-s">' + snippet(e) + '</span></a>');
      });
      if (group.length > k[2]) out.push('<p class="res-count">' + (group.length - k[2]) + ' more. Add a word to narrow the search.</p>');
    });
    panel.innerHTML = out.join('');
  }
  function openResults() { panel.hidden = false; q.setAttribute('aria-expanded', 'true'); }
  function closeResults() { panel.hidden = true; q.setAttribute('aria-expanded', 'false'); }
  function clearMarks() { if (window.CSS && CSS.highlights) CSS.highlights.delete('hit'); }
  function markIn(el) {
    if (!(window.CSS && CSS.highlights && window.Highlight) || !tokens.length) return;
    var h = new Highlight(), walker = doc.createTreeWalker(el, NodeFilter.SHOW_TEXT), n;
    while ((n = walker.nextNode())) {
      var f = fold(n.nodeValue);
      tokens.forEach(function (t) {
        var i = f.indexOf(t);
        while (i !== -1) {
          var r = doc.createRange();
          r.setStart(n, i); r.setEnd(n, i + t.length);
          h.add(r);
          i = f.indexOf(t, i + t.length);
        }
      });
    }
    CSS.highlights.set('hit', h);
  }
  var timer = null;
  function run() {
    var v = squash(q.value);
    if (v.length < 2) { closeResults(); clearMarks(); return; }
    render(find(v), v);
    openResults();
  }
  q.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 120); });
  q.addEventListener('focus', function () { if (squash(q.value).length >= 2) run(); });
  q.addEventListener('keydown', function (e) {
    var first = $('.res', panel);
    if (e.key === 'ArrowDown' && first && !panel.hidden) { e.preventDefault(); first.focus(); }
    else if (e.key === 'Enter' && first && !panel.hidden) { e.preventDefault(); first.click(); }
    else if (e.key === 'Escape') {
      if (!panel.hidden) closeResults(); else { q.value = ''; clearMarks(); }
    }
  });
  panel.addEventListener('keydown', function (e) {
    var items = $$('.res', panel), i = items.indexOf(doc.activeElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); (items[i + 1] || items[i] || items[0]).focus(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); if (i <= 0) q.focus(); else items[i - 1].focus(); }
    else if (e.key === 'Escape') { closeResults(); q.focus(); }
  });
  panel.addEventListener('click', function (e) {
    var a = e.target.closest('a.res');
    if (!a) return;
    closeResults();
    q.blur();
    var t = doc.getElementById(a.getAttribute('href').slice(1));
    if (t) {
      if (t.classList.contains('pt') && root.getAttribute('data-view') === 'actions') {
        t.classList.add('show-all');
        var more = $('.pt-more', t);
        if (more) { more.setAttribute('aria-expanded', 'true'); more.textContent = 'Hide the full explanation'; }
      }
      setTimeout(function () { markIn(t); flash(t); }, 0);
    }
  });
  doc.addEventListener('click', function (e) { if (!e.target.closest('.search')) closeResults(); });
  doc.addEventListener('keydown', function (e) {
    if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      var t = e.target;
      if (t.closest && t.closest('input, textarea, select, [contenteditable="true"]')) return;
      e.preventDefault(); q.focus(); q.select();
    } else if (e.key === 'Escape' && root.classList.contains('toc-open')) {
      openToc(false); menuBtn.focus();
    }
  });

  /* ---------- slide checklist (ticks stay in this browser) ---------- */
  var boxes = $$('#your-slide-checklist input[type="checkbox"]');
  if (boxes.length) {
    var saved = [];
    try { saved = JSON.parse(store.get('abotrt.checklist') || '[]'); } catch (e) { saved = []; }
    var resetBtn = $('#ckReset'), armed = null;
    var updateCk = function () {
      var on = boxes.filter(function (b) { return b.checked; }).map(function (b) { return b.id; });
      store.set('abotrt.checklist', JSON.stringify(on));
      $('#ckCount').textContent = on.length + ' of ' + boxes.length + ' done';
      $('#ckBar').style.width = (100 * on.length / boxes.length) + '%';
      resetBtn.hidden = on.length === 0;
    };
    boxes.forEach(function (b) {
      if (saved.indexOf(b.id) !== -1) b.checked = true;
      b.addEventListener('change', updateCk);
    });
    resetBtn.addEventListener('click', function () {
      if (!armed) {
        resetBtn.textContent = 'Tap again to clear every tick';
        armed = setTimeout(function () { armed = null; resetBtn.textContent = 'Clear ticks'; }, 3500);
        return;
      }
      clearTimeout(armed); armed = null; resetBtn.textContent = 'Clear ticks';
      boxes.forEach(function (b) { b.checked = false; });
      updateCk();
    });
    updateCk();
  }
})();
