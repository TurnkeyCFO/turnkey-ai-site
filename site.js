/* Turnkey AI — site behaviors */

// Reveal-on-scroll (with safety net: anything still hidden after 2.5s gets revealed)
(function () {
  const els = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add('is-visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -4% 0px' });
  els.forEach((el) => io.observe(el));
  // Safety net for headless capture / non-scroll contexts
  setTimeout(() => {
    document.querySelectorAll('.reveal:not(.is-visible)').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 1.2) el.classList.add('is-visible');
    });
  }, 600);
  // Reduced motion: reveal everything immediately
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'));
  }
})();

// Generate dotted pulse-wave fields in the background SVGs
(function () {
  const waves = document.querySelectorAll('.wave-svg');
  if (!waves.length) return;

  waves.forEach((svg, waveIndex) => {
    const dotGroup = svg.querySelector('.wave-dots');
    if (!dotGroup) return;

    const W = 1600, H = 400;
    const cols = 90;
    const phase = waveIndex * Math.PI;

    for (let c = 0; c < cols; c++) {
      const x = (c / (cols - 1)) * W;
      // Stacked sine waves for organic "pulse-field" feel
      const a1 = Math.sin((c / cols) * Math.PI * 4 + phase) * 60;
      const a2 = Math.sin((c / cols) * Math.PI * 2 + phase * 1.7) * 40;
      const baseY = H / 2 + a1 + a2;

      // How many dots stack vertically — varies for irregularity
      const stack = 4 + Math.floor(Math.abs(Math.sin((c / cols) * Math.PI * 6)) * 6);

      for (let s = 0; s < stack; s++) {
        const y = baseY + (s - stack / 2) * 10;
        const r = 1.2 + (s === Math.floor(stack / 2) ? 0.6 : 0);
        const op = 0.18 + (s === Math.floor(stack / 2) ? 0.55 : Math.random() * 0.35);
        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.setAttribute('cx', x.toFixed(1));
        dot.setAttribute('cy', y.toFixed(1));
        dot.setAttribute('r', r.toFixed(2));
        dot.setAttribute('fill', s === Math.floor(stack / 2) ? '#0052FF' : '#2C7DFF');
        dot.setAttribute('opacity', (op * 0.5).toFixed(2));
        dotGroup.appendChild(dot);
      }
    }

    // Animate the wave group slowly so it feels alive
    let t = waveIndex * 1000;
    function tick() {
      t += 16;
      const tx = Math.sin(t / 6000) * 30;
      dotGroup.setAttribute('transform', `translate(${tx} 0)`);
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
})();

// Stat count-up
(function () {
  const stats = document.querySelectorAll('.fact-row strong, .system-stats strong, .readout-value');
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      const el = e.target;
      const raw = el.textContent.trim();
      const match = raw.match(/^([\d.,]+)(.*)$/);
      if (!match) { io.unobserve(el); return; }
      const target = parseFloat(match[1].replace(/,/g, ''));
      const suffix = match[2];
      if (isNaN(target)) { io.unobserve(el); return; }

      const dur = 1100;
      const start = performance.now();
      const decimals = (match[1].split('.')[1] || '').length;
      function step(now) {
        const p = Math.min(1, (now - start) / dur);
        const eased = 1 - Math.pow(1 - p, 3);
        const val = target * eased;
        const formatted = decimals ? val.toFixed(decimals) : Math.floor(val).toLocaleString();
        el.textContent = formatted + suffix;
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
      io.unobserve(el);
    });
  }, { threshold: 0.5 });
  stats.forEach((s) => io.observe(s));
})();

// Smooth-scroll for in-page anchors with sticky-header offset
(function () {
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href').slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      const y = target.getBoundingClientRect().top + window.pageYOffset - 80;
      window.scrollTo({ top: y, behavior: 'smooth' });
    });
  });
})();
