(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Поява карток при скролі ---------- */
  var items = $$('.reveal');
  function reveal(el) {
    el.style.setProperty('--d', ((parseInt(el.style.getPropertyValue('--i'), 10) || 0) % 3) * 90 + 'ms');
    el.classList.add('in');
    el.addEventListener('transitionend', function done(e) {
      if (e.propertyName !== 'opacity') return;
      el.removeEventListener('transitionend', done);
      el.classList.remove('reveal', 'in');       // після появи повертаємо звичайний hover
      el.style.removeProperty('--d');
    });
  }
  if (items.length) {
    if ('IntersectionObserver' in window && !reduce) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { io.unobserve(en.target); reveal(en.target); }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
      items.forEach(function (el) { io.observe(el); });
    } else {
      items.forEach(function (el) { el.classList.remove('reveal'); });
    }
  }

  /* ---------- Лічильник у hero ---------- */
  $$('[data-count]').forEach(function (el) {
    var end = parseInt(el.dataset.count, 10);
    if (!end || reduce) return;
    var t0 = null, dur = 1200;
    function step(t) {
      if (t0 === null) t0 = t;
      var p = Math.min((t - t0) / dur, 1);
      el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    }
    el.textContent = '0';
    requestAnimationFrame(step);
  });

  /* ---------- Hero-слайдшоу ---------- */
  var hero = $('.hero');
  if (hero) {
    var cap = $('.hero-caption'), dots = $$('.hero-dots i'), cur = 0, timer;
    var slides = function () { return $$('.hero-slide', hero); };
    function go(n) {
      var list = slides();
      if (!list.length) return;
      cur = (n + list.length) % list.length;
      list.forEach(function (s, k) { s.classList.toggle('active', k === cur); });
      dots.forEach(function (d, k) { d.classList.toggle('on', k === cur); });
      if (cap) {
        var d = list[cur].dataset;
        cap.href = d.href;
        $('.hc-name', cap).textContent = d.name;
        $('.hc-meta', cap).textContent = d.meta;
        $('.hc-price', cap).textContent = d.price;
      }
    }
    function start() {
      clearInterval(timer);
      if (slides().length > 1 && !reduce) timer = setInterval(function () { go(cur + 1); }, 6500);
    }
    dots.forEach(function (d, k) {
      d.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); go(k); start(); });
    });
    start();
  }

  /* ---------- Обране (зберігається в браузері) ---------- */
  var KEY = 'autovault_fav', fav = [];
  try { fav = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { fav = []; }
  $$('.fav').forEach(function (b) {
    var id = parseInt(b.dataset.id, 10);
    b.classList.toggle('on', fav.indexOf(id) > -1);
    b.addEventListener('click', function (e) {
      e.preventDefault();
      var i = fav.indexOf(id);
      if (i > -1) fav.splice(i, 1); else fav.push(id);
      try { localStorage.setItem(KEY, JSON.stringify(fav)); } catch (err) {}
      b.classList.toggle('on', i === -1);
      b.setAttribute('aria-label', i === -1 ? 'Прибрати з обраного' : 'Додати в обране');
      b.classList.remove('pop'); void b.offsetWidth; b.classList.add('pop');
    });
  });

  /* ---------- Галерея + лайтбокс ---------- */
  var gal = $('.gallery'), dataEl = $('#gallery-data');
  if (gal && dataEl) {
    var imgs = JSON.parse(dataEl.textContent), idx = 0;
    var mainImg = $('.gallery-open img', gal), counter = $('.gallery-count', gal), thumbs = $$('.thumb', gal);
    var lb = $('#lightbox'), lbImg = $('.lb-img', lb), lbCount = $('.lb-count', lb);

    function show(n) {
      idx = (n + imgs.length) % imgs.length;
      mainImg.style.opacity = 0;
      setTimeout(function () { mainImg.src = imgs[idx]; mainImg.style.opacity = 1; }, 120);
      thumbs.forEach(function (t, k) { t.classList.toggle('active', k === idx); });
      if (thumbs[idx]) thumbs[idx].scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: reduce ? 'auto' : 'smooth' });
      if (counter) counter.textContent = (idx + 1) + ' / ' + imgs.length;
      if (lb.classList.contains('open')) paintLb(true);
    }
    function paintLb(anim) {
      function set() { lbImg.src = imgs[idx]; lbImg.classList.remove('swap'); }
      lbCount.textContent = imgs.length > 1 ? (idx + 1) + ' / ' + imgs.length : '';
      if (anim) { lbImg.classList.add('swap'); setTimeout(set, 160); } else set();
      var nxt = new Image(); nxt.src = imgs[(idx + 1) % imgs.length];   // підвантажуємо наступне
    }
    function openLb() {
      lb.classList.add('open'); lb.setAttribute('aria-hidden', 'false');
      document.body.classList.add('no-scroll');
      paintLb(false);
      requestAnimationFrame(function () { lb.classList.add('show'); });
    }
    function closeLb() {
      lb.classList.remove('show'); lb.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('no-scroll');
      setTimeout(function () { lb.classList.remove('open'); }, 250);
    }

    $('.gallery-open', gal).addEventListener('click', openLb);
    thumbs.forEach(function (t) { t.addEventListener('click', function () { show(parseInt(t.dataset.i, 10)); }); });
    var gp = $('.gnav.prev', gal), gn = $('.gnav.next', gal);
    if (gp) gp.addEventListener('click', function () { show(idx - 1); });
    if (gn) gn.addEventListener('click', function () { show(idx + 1); });

    $('.lb-close', lb).addEventListener('click', closeLb);
    var lp = $('.lb-prev', lb), ln = $('.lb-next', lb);
    if (lp) lp.addEventListener('click', function () { show(idx - 1); });
    if (ln) ln.addEventListener('click', function () { show(idx + 1); });
    lb.addEventListener('click', function (e) {
      if (e.target === lb || e.target.classList.contains('lb-stage')) closeLb();
    });
    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') closeLb();
      else if (e.key === 'ArrowLeft') show(idx - 1);
      else if (e.key === 'ArrowRight') show(idx + 1);
    });
    // свайп на телефоні
    var x0 = null;
    lb.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 50 && imgs.length > 1) show(idx + (dx < 0 ? 1 : -1));
    });
  }
})();
