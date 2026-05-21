/* ════════════════════════════════════════════════════════════════
   Turnkey AI — zoom-forward scroll engine + panel interactions.

   The mechanic: 7 panels sit stacked in z-space inside a fixed
   perspective stage. A tall invisible #scroll-driver gives the page
   real height; scrolling moves a virtual "camera" forward. Each
   panel's distance from the camera (d) becomes a translateZ — so the
   next panel rushes up out of the cosmos while the current one blows
   past your face and fades. Native scroll drives it (wheel, trackpad,
   keys, touch all free); the camera position is eased for a
   cinematic, non-jumpy feel.
   ════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var panels  = Array.prototype.slice.call(document.querySelectorAll('.panel'));
  var N       = panels.length;                       // 7
  var driver  = document.getElementById('scroll-driver');
  var rail    = document.querySelectorAll('.rail-step');
  var hint    = document.getElementById('scrollHint');

  var REDUCE  = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── Tuning ──────────────────────────────────────────────────────
  var PANEL_VH = 122;            // scroll distance allotted per panel
  var GAP      = REDUCE ? 0 : 980;   // z-distance between panels (px)
  var EASE     = REDUCE ? 1 : 0.105; // camera follow easing per frame

  driver.style.height = (N * PANEL_VH) + 'vh';

  // ── Camera state ────────────────────────────────────────────────
  var camTarget = 0;   // where the scroll says the camera should be
  var camNow    = 0;   // eased actual camera position
  var maxScroll = 1;

  function recalcScroll() {
    maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
  }
  recalcScroll();

  // ── Fit-to-viewport ─────────────────────────────────────────────
  // Each panel is a fixed-size card. Measure its content and scale the
  // inner block down if it would overflow the frame — so the deck is
  // bulletproof on any screen without hand-tuning every panel.
  function fitPanels() {
    for (var i = 0; i < N; i++) {
      var panel = panels[i];
      var prev  = panel.style.display;
      panel.style.display = 'flex';
      var inner = panel.querySelector('.panel-inner');
      inner.style.transform = 'none';
      var h  = inner.offsetHeight;
      var cs = getComputedStyle(panel);
      var room = window.innerHeight
               - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
      var scale = (h > room && h > 0) ? Math.max(0.6, room / h) : 1;
      inner.style.transform = scale < 1 ? 'scale(' + scale.toFixed(4) + ')' : '';
      panel.style.display = prev;          // render() will set it correctly
    }
  }
  fitPanels();
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(fitPanels);  // re-fit once the webfont lands
  }

  var resizeT = 0;
  window.addEventListener('resize', function () {
    recalcScroll();
    clearTimeout(resizeT);
    resizeT = setTimeout(fitPanels, 120);
  });

  function readScroll() {
    var p = Math.min(1, Math.max(0, window.scrollY / maxScroll));
    camTarget = p * (N - 1);
  }
  window.addEventListener('scroll', readScroll, { passive: true });
  readScroll();
  camNow = camTarget;

  // ── Math helpers ────────────────────────────────────────────────
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function ss(a, b, x) {                       // smoothstep
    var t = clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  }

  // ── The render — places every panel for the current camera ──────
  var litDone = false;          // services-panel stagger-light guard

  function render() {
    for (var i = 0; i < N; i++) {
      var panel = panels[i];
      var d  = camNow - i;                     // <0 ahead · 0 here · >0 passed
      var ad = Math.abs(d);

      // opacity: hold dark until the panel is close, then fade up from
      // the depths; fade out fast as it rushes past the camera. The
      // tight near-side window keeps the next panel from ghosting
      // through the one you're reading.
      var op = ss(-0.94, -0.30, d) * (1 - ss(0.18, 0.88, d));

      if (op <= 0.004) {                       // off-camera — skip it
        if (panel.style.display !== 'none') panel.style.display = 'none';
        continue;
      }
      if (panel.style.display === 'none') panel.style.display = 'flex';

      var z  = d * GAP;                        // translateZ along camera axis
      var ty = REDUCE ? 0 : d * -22;           // a hair of vertical drift
      // motion blur as it blows past, faint soft-focus far in the depths
      var blur = REDUCE ? 0
               : clamp((d - 0.14) * 8, 0, 9) + clamp((-d - 0.55) * 4, 0, 2.5);

      panel.style.transform = 'translate3d(0,' + ty.toFixed(1) + 'px,0) translateZ('
                            + z.toFixed(1) + 'px)';
      panel.style.opacity   = op.toFixed(3);
      panel.style.filter    = blur > 0.05 ? 'blur(' + blur.toFixed(2) + 'px)' : 'none';
      panel.style.zIndex    = Math.round((d + 2) * 50);
      // only the panel under the camera takes clicks
      panel.style.pointerEvents = (ad < 0.42 && op > 0.55) ? 'auto' : 'none';
    }

    // active rail marker
    var active = Math.round(camNow);
    for (var r = 0; r < rail.length; r++) {
      rail[r].classList.toggle('is-active', r === active);
    }

    // services panel (#c2 = index 2) — stagger-light the four cards
    if (Math.abs(camNow - 2) < 0.45) {
      if (!litDone) { litDone = true; lightServices(); }
    } else if (litDone && Math.abs(camNow - 2) > 0.9) {
      litDone = false; unlightServices();
    }

    // background drift + scroll hint
    if (window.__aurora) window.__aurora.setScroll(camNow / (N - 1));
    if (hint) hint.classList.toggle('gone', camNow > 0.18);
  }

  // ── Always-on rAF loop — eases the camera, repaints panels ──────
  var loopOn = true;
  function loop() {
    if (!loopOn) return;
    camNow += (camTarget - camNow) * EASE;
    if (Math.abs(camTarget - camNow) < 0.0004) camNow = camTarget;
    render();
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // Debug hook — snap the camera to an exact position and repaint.
  // Used only by the screenshot harness; harmless (unused) in the wild.
  window.__cam = function (v) { camTarget = v; camNow = v; render(); };

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { loopOn = false; }
    else if (!loopOn) { loopOn = true; requestAnimationFrame(loop); }
  });

  // ── Jump-to-panel (rail, nav, hero CTA) ─────────────────────────
  function jumpTo(i) {
    recalcScroll();
    var top = (clamp(i, 0, N - 1) / (N - 1)) * maxScroll;
    window.scrollTo({ top: top, behavior: REDUCE ? 'auto' : 'smooth' });
  }
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-jump]');
    if (!el) return;
    e.preventDefault();
    jumpTo(parseInt(el.getAttribute('data-jump'), 10) || 0);
  });

  // ── Services lighting ───────────────────────────────────────────
  var serviceEls = document.querySelectorAll('#c2 .service');
  var litTimers = [];
  function lightServices() {
    litTimers.forEach(clearTimeout); litTimers = [];
    serviceEls.forEach(function (el, k) {
      litTimers.push(setTimeout(function () { el.classList.add('is-lit'); },
        REDUCE ? 0 : 160 + k * 230));
    });
  }
  function unlightServices() {
    litTimers.forEach(clearTimeout); litTimers = [];
    serviceEls.forEach(function (el) { el.classList.remove('is-lit'); });
  }

  // ── FAQ accordion ───────────────────────────────────────────────
  var faqList = document.getElementById('faqList');
  if (faqList) {
    faqList.addEventListener('click', function (e) {
      var row = e.target.closest('.faq-row');
      if (!row) return;
      var open = row.classList.contains('is-open');
      faqList.querySelectorAll('.faq-row').forEach(function (r) {
        r.classList.remove('is-open');
      });
      if (!open) row.classList.add('is-open');
    });
  }

  // ── Live strategy showcase ──────────────────────────────────────
  var STRATEGIES = {
    dental: [
      { h: 'Wedge', b: 'The front desk loses hours to insurance verification and recall calls — that’s the first place to put AI to work.' },
      { h: 'Quick win — week 1–2', b: 'A verification agent that checks coverage overnight, so every morning chart is ready before the first patient.' },
      { h: 'Agent — month 1–3', b: 'A recall-and-reschedule agent that texts lapsed patients in your voice and books them straight into the open chair.' },
      { h: 'What you’ll feel', b: 'Front desks stop chasing phones, the schedule fills itself, and no-show gaps close on their own.' }
    ],
    roaster: [
      { h: 'Wedge', b: 'Wholesale orders arrive as emails, texts, and PDFs — getting them into one clean queue is the highest-leverage fix.' },
      { h: 'Quick win — week 1–2', b: 'An intake agent that reads every order channel into a single dashboard your roaster checks once a day.' },
      { h: 'Agent — month 1–3', b: 'A reorder agent that watches each account’s cadence and drafts the next order before the café runs dry.' },
      { h: 'What you’ll feel', b: 'Fewer missed reorders, no more retyping orders by hand, and wholesale that grows without another hire.' }
    ],
    law: [
      { h: 'Wedge', b: 'Associates burn days assembling and checking case packets — document handling is where AI pays for itself first.' },
      { h: 'Quick win — week 1–2', b: 'An intake agent that turns a client’s documents into a complete, gap-flagged checklist on day one.' },
      { h: 'Agent — month 1–3', b: 'A drafting agent that assembles first-pass filings from your templates and the client’s record, ready for attorney review.' },
      { h: 'What you’ll feel', b: 'Cases move faster, packets stop coming back incomplete, and attorneys spend their hours on argument, not assembly.' }
    ],
    hvac: [
      { h: 'Wedge', b: 'The dispatcher’s morning — triaging tickets and routing trucks — is the bottleneck AI should take over first.' },
      { h: 'Quick win — week 1–2', b: 'A triage agent that sorts overnight tickets by urgency and drafts the day’s routes before anyone clocks in.' },
      { h: 'Agent — month 1–3', b: 'A customer agent that confirms appointments, answers status questions, and texts ETAs without pulling a tech off a job.' },
      { h: 'What you’ll feel', b: 'Dispatch runs calm, trucks spend more time on calls than driving, and customers stop wondering when you’ll show.' }
    ]
  };
  var CUSTOM = [
    { h: 'Where to start', b: 'The honest answer: the sharp version of this needs ten minutes with you, not a text box — every operation hides its wedge somewhere different.' },
    { h: 'Next step', b: 'Book a 30-minute call below. We’ll sketch your wedge, your two-week win, and the first agent live — and you keep the notes.' }
  ];

  var aiForm  = document.getElementById('aiForm');
  var aiText  = document.getElementById('aiText');
  var aiRun   = document.getElementById('aiRun');
  var aiOut   = document.getElementById('aiOut');
  var aiState = document.getElementById('aiState');
  var typing  = false;

  function setState(s) { if (aiState) aiState.textContent = s; }

  // Build the block shells, then type each body in sequence.
  function showStrategy(blocks, withCTA) {
    if (typing) return;
    typing = true;
    setState('Thinking');
    aiOut.innerHTML = '';
    var bodies = [];
    blocks.forEach(function (blk) {
      var wrap = document.createElement('div');
      wrap.className = 'strat-block';
      var h = document.createElement('div');
      h.className = 'sh'; h.textContent = blk.h;
      var b = document.createElement('div');
      b.className = 'sb';
      wrap.appendChild(h); wrap.appendChild(b);
      aiOut.appendChild(wrap);
      bodies.push({ el: b, text: blk.b });
    });

    function finish() {
      typing = false;
      setState('Ready');
      if (withCTA) {
        var cta = document.createElement('a');
        cta.className = 'cta book-cta strat-cta';
        cta.href = 'https://calendly.com/ricky-turnkeycfo/15min-intro-call';
        cta.target = '_blank';
        cta.rel = 'noopener';
        cta.innerHTML = '<span>Book the 15-minute intro call</span><span class="cta-arrow">→</span>';
        aiOut.appendChild(cta);
      }
    }

    if (REDUCE) {                              // no typing animation
      bodies.forEach(function (x) { x.el.textContent = x.text; });
      finish();
      return;
    }

    var bi = 0;
    function typeBlock() {
      if (bi >= bodies.length) { finish(); return; }
      var cur = bodies[bi], ci = 0;
      var caret = document.createElement('span');
      caret.className = 'caret';
      cur.el.appendChild(caret);
      (function step() {
        ci += 2;
        cur.el.textContent = cur.text.slice(0, ci);
        if (ci < cur.text.length) {
          cur.el.appendChild(caret);
          setTimeout(step, 12);
        } else {
          cur.el.textContent = cur.text;
          bi++;
          setTimeout(typeBlock, 130);
        }
      })();
    }
    typeBlock();
  }

  if (aiOut) {
    aiOut.addEventListener('click', function (e) {
      var chip = e.target.closest('.chip');
      if (!chip || typing) return;
      var key = chip.getAttribute('data-ex');
      if (aiText) aiText.value = chip.textContent.trim();
      showStrategy(STRATEGIES[key], false);
    });
  }
  // POST the free-text input to /api/strategize (Cloudflare Pages
  // Function → OpenRouter Sonnet 4.6) and render the 4-block sketch.
  // On any failure, fall back to the deterministic CUSTOM block so the
  // section always says something useful.
  function liveStrategize(business) {
    if (typing) return;
    typing = true;
    setState('Thinking');
    aiOut.innerHTML = '';
    // fun thinking animation — orbiting brand-blue dots + rotating phase copy
    var thinker = document.createElement('div');
    thinker.className = 'thinker';
    thinker.setAttribute('aria-live', 'polite');
    thinker.innerHTML =
      '<div class="thinker-orb">' +
        '<span class="ring r1"></span>' +
        '<span class="ring r2"></span>' +
        '<span class="dot d1"></span>' +
        '<span class="dot d2"></span>' +
        '<span class="dot d3"></span>' +
        '<span class="core"></span>' +
      '</div>' +
      '<div class="thinker-phase">Reading your business…</div>' +
      '<div class="thinker-sub">Sonnet 4.6 is sketching your wedge live</div>';
    aiOut.appendChild(thinker);

    var phases = [
      'Reading your business…',
      'Finding where the hours bleed…',
      'Naming the wedge…',
      'Sketching the two-week win…',
      'Designing the agent…',
      'Writing it up…'
    ];
    var phaseEl = thinker.querySelector('.thinker-phase');
    var pIdx = 0;
    var phaseTimer = setInterval(function () {
      pIdx = (pIdx + 1) % phases.length;
      if (!phaseEl) return;
      phaseEl.classList.add('swap');
      setTimeout(function () {
        phaseEl.textContent = phases[pIdx];
        phaseEl.classList.remove('swap');
      }, 220);
    }, 1600);

    var done = false;
    function stopThinker() { clearInterval(phaseTimer); }
    var safety = setTimeout(function () {
      if (done) return;
      done = true;
      typing = false;
      stopThinker();
      aiOut.innerHTML = '';
      showStrategy(CUSTOM, true);
    }, 16000);

    fetch('/api/strategize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ business: business })
    })
    .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
    .then(function (res) {
      if (done) return;
      done = true;
      clearTimeout(safety);
      stopThinker();
      typing = false;
      aiOut.innerHTML = '';
      if (res.ok && res.j && Array.isArray(res.j.blocks) && res.j.blocks.length) {
        showStrategy(res.j.blocks, true);
      } else {
        showStrategy(CUSTOM, true);
      }
    })
    .catch(function () {
      if (done) return;
      done = true;
      clearTimeout(safety);
      stopThinker();
      typing = false;
      aiOut.innerHTML = '';
      showStrategy(CUSTOM, true);
    });
  }

  if (aiForm) {
    aiForm.addEventListener('submit', function (e) {
      e.preventDefault();
      if (typing) return;
      var v = (aiText.value || '').trim();
      if (!v) return;
      liveStrategize(v);
    });
  }

  // ── Auto-hide the scroll hint after a while ─────────────────────
  setTimeout(function () { if (hint) hint.classList.add('gone'); }, 8000);
})();
