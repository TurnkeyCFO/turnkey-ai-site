# Turnkey AI — Landing Page

Conversion-oriented landing page for **Turnkey AI** — practical AI tools for service businesses doing $1M–$5M in revenue.

## Stack

Plain HTML, CSS, JS. No build step. Hosts on GitHub Pages.

- `index.html` — page markup
- `styles.css` — design system + sections
- `site.js` — reveal animations, pulse-wave generator, count-up
- `assets/` — brand assets

## Local preview

```bash
python -m http.server 8741
# → http://127.0.0.1:8741
```

## Brand

Light theme. Plus Jakarta Sans only. Electric blue accents (`#0052FF` primary, `#0037C9` deep, `#5BC6FF` icy). See the inline gradient defs at the top of `index.html` for the canonical electric-blue gradient.

## Calendly

Booking widget embedded in the CTA section. Update the `data-url` attribute on the `.calendly-inline-widget` to swap accounts.
