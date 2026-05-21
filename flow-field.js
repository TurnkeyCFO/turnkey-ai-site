/* ════════════════════════════════════════════════════════════════
   Flow-field background — vanilla port of the React/canvas
   neural-flow component. Light-first, Turnkey AI blue.

   • 2D canvas (no WebGL).
   • Light trail fade — particles deposit blue dots on a near-white
     surface that very slowly re-bleaches itself, leaving long
     wispy trails without ever going dark.
   • Two-tone particles: deep #0037C9 + cyan #5FB1FF mixed by lane.
   • Mouse repulsion within 150px.
   • window.__aurora.setScroll(p) keeps API parity with the old
     aurora — scroll drifts the flow field forward.
   ════════════════════════════════════════════════════════════════ */
(function () {
  var canvas = document.getElementById('aurora');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  if (!ctx) return;

  // -------- tunables -------------------------------------------------
  var PARTICLE_COUNT = 520;            // fewer particles → cleaner type
  var SPEED          = 0.9;
  var TRAIL_ALPHA    = 0.085;          // higher = faster bleach, shorter trails
  var TRAIL_RGB      = '250, 250, 252';// the bleach (matches body bg)
  var INTERACT_R     = 150;
  var COLOR_DEEP     = [0, 55, 201];   // #0037C9
  var COLOR_CYAN     = [95, 177, 255]; // #5FB1FF
  var REDUCE = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // -------- size + DPR ----------------------------------------------
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var W = 0, H = 0;

  function fit() {
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.style.width  = W + 'px';
    canvas.style.height = H + 'px';
    canvas.width  = Math.max(2, Math.floor(W * dpr));
    canvas.height = Math.max(2, Math.floor(H * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // prime with the bleach color so the first frames aren't black
    ctx.fillStyle = 'rgb(' + TRAIL_RGB + ')';
    ctx.fillRect(0, 0, W, H);
  }
  fit();
  window.addEventListener('resize', fit);

  // -------- mouse ----------------------------------------------------
  var mx = -1e4, my = -1e4;
  window.addEventListener('mousemove', function (e) { mx = e.clientX; my = e.clientY; });
  window.addEventListener('mouseleave', function () { mx = -1e4; my = -1e4; });

  // -------- scroll uniform ------------------------------------------
  var scrollTarget = 0, scrollEased = 0;
  window.__aurora = { setScroll: function (p) { scrollTarget = p; } };
  // legacy name too, in case anything later refers to it
  window.__flowfield = window.__aurora;

  // -------- particles ------------------------------------------------
  function rand(n) { return Math.random() * n; }
  function P() { this.reset(true); }
  P.prototype.reset = function (initial) {
    this.x   = rand(W);
    this.y   = rand(H);
    this.vx  = 0;
    this.vy  = 0;
    this.age = initial ? rand(180) : 0;
    this.life= rand(220) + 120;
    // bias toward deep blue, occasional cyan accent particle
    this.cyan = Math.random() < 0.22;
  };
  P.prototype.step = function (s) {
    // flow angle — same math as the source, plus a scroll drift
    var a = (Math.cos(this.x * 0.005 + s * 0.6) + Math.sin(this.y * 0.005 - s * 0.4)) * Math.PI;
    this.vx += Math.cos(a) * 0.20 * SPEED;
    this.vy += Math.sin(a) * 0.20 * SPEED;

    // mouse repulsion
    var dx = mx - this.x, dy = my - this.y;
    var d  = Math.sqrt(dx*dx + dy*dy);
    if (d < INTERACT_R) {
      var f = (INTERACT_R - d) / INTERACT_R;
      this.vx -= dx * f * 0.05;
      this.vy -= dy * f * 0.05;
    }

    this.x += this.vx;
    this.y += this.vy;
    this.vx *= 0.95;
    this.vy *= 0.95;

    this.age++;
    if (this.age > this.life) this.reset(false);

    if (this.x < 0) this.x = W; else if (this.x > W) this.x = 0;
    if (this.y < 0) this.y = H; else if (this.y > H) this.y = 0;
  };
  P.prototype.draw = function () {
    // age curve: fade in, hold, fade out
    var k = this.age / this.life;
    var alpha = 1 - Math.abs(k - 0.5) * 2;
    alpha *= 0.42;                       // overall intensity (light bg needs restraint)
    if (alpha <= 0.01) return;
    var c = this.cyan ? COLOR_CYAN : COLOR_DEEP;
    ctx.fillStyle = 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + alpha.toFixed(3) + ')';
    ctx.fillRect(this.x, this.y, 1.6, 1.6);
  };

  var ps = [];
  for (var i = 0; i < PARTICLE_COUNT; i++) ps.push(new P());

  // -------- loop -----------------------------------------------------
  var running = true;
  function frame() {
    if (!running) return;

    // light bleach instead of dark fade — slowly returns the canvas to
    // body background, leaving wispy blue trails behind each particle
    ctx.fillStyle = 'rgba(' + TRAIL_RGB + ',' + TRAIL_ALPHA + ')';
    ctx.fillRect(0, 0, W, H);

    if (REDUCE) {
      requestAnimationFrame(frame);
      return;
    }

    scrollEased += (scrollTarget - scrollEased) * 0.06;
    for (var i = 0; i < ps.length; i++) {
      ps[i].step(scrollEased);
      ps[i].draw();
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      running = false;
    } else if (!running) {
      running = true;
      requestAnimationFrame(frame);
    }
  });
})();
