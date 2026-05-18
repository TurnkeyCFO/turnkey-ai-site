"""
build_industries.py — renders the Turnkey AI industry sub-pages.

Reads every industries/<slug>.json data file and renders:
  ../industries/<slug>/index.html   (30 industry pages)
  ../industries/index.html          (industry hub)
  ../blog/index.html                (blog hub, empty-state)
  ../blog/blog-styles.css           (blog styles)
  ../sitemap.xml
  ../robots.txt

It also patches the home ../index.html nav + footer to link Industries & Blog.

Plain-Python string templating — no build step, no heavy deps. Re-runnable
and idempotent: re-running overwrites the generated files cleanly.

Usage:  python build_industries.py
"""
from __future__ import annotations

import html as _html
import json
import re
from datetime import date
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths & config
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent          # _industry-builder/
SITE = HERE.parent                              # turnkey-ai-local/  (site root)
DATA = HERE / "industries"                      # JSON data files

# GitHub Pages project site — served under /turnkey-ai-site/.
# If a CNAME custom domain exists, switch to it (served at domain root).
CNAME = SITE / "CNAME"
if CNAME.exists():
    _domain = CNAME.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    BASE_URL = f"https://{_domain}"
    ROOT = ""                                   # custom domain serves at root
else:
    BASE_URL = "https://turnkeycfo.github.io/turnkey-ai-site"
    ROOT = "/turnkey-ai-site"                   # project-site path prefix

CALENDLY = "https://calendly.com/ricky-turnkeycfo/15min-intro-call"
EMAIL = "Ricky@turnkeyservices.com"
YEAR = date.today().year

GROUP_ORDER = ["Home Services", "Auto", "Personal Care & Wellness", "Trades & Specialty"]


def esc(s: str) -> str:
    """HTML-escape text content."""
    return _html.escape(str(s), quote=True)


def jstr(s: str) -> str:
    """JSON-string-escape for embedding inside JSON-LD."""
    return json.dumps(str(s))[1:-1]


# ----------------------------------------------------------------------------
# Shared chrome — gradient defs, header, footer
# ----------------------------------------------------------------------------

GRAD_DEFS = """  <svg style="position:absolute;width:0;height:0;overflow:hidden;" aria-hidden="true">
    <defs>
      <linearGradient id="tk-electric" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0%" stop-color="#0037C9"/>
        <stop offset="55%" stop-color="#005EFF"/>
        <stop offset="100%" stop-color="#8CE8FF"/>
      </linearGradient>
      <linearGradient id="tk-electric-h" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#0037C9"/>
        <stop offset="50%" stop-color="#005EFF"/>
        <stop offset="100%" stop-color="#7DE0FF"/>
      </linearGradient>
    </defs>
  </svg>"""

BRAND_MARK = """<svg class="brand-mark" viewBox="0 0 64 64" aria-hidden="true">
            <rect x="8" y="10" width="40" height="6" fill="url(#tk-electric)"/>
            <rect x="25" y="10" width="6" height="44" fill="url(#tk-electric)"/>
            <path d="M 36 14 L 56 14 L 36 32 L 56 54 L 36 54 L 22 38 Z" fill="url(#tk-electric)" opacity="0.95"/>
          </svg>"""


def header(home: str) -> str:
    """Site header. `home` is the root-relative path to index.html."""
    return f"""    <header class="topbar">
      <div class="container topbar-inner">
        <a class="brand-lockup" href="{home}" aria-label="Turnkey AI home">
          {BRAND_MARK}
          <div class="brand-words">
            <span class="brand-name">TURNKEY</span>
            <span class="brand-sub">AI</span>
          </div>
        </a>
        <nav class="desktop-nav" aria-label="Primary">
          <a href="{home}#what-we-do">What we do</a>
          <a href="{ROOT}/industries/">Industries</a>
          <a href="{home}#pricing">Pricing</a>
          <a href="{ROOT}/blog/">Blog</a>
          <a href="{home}#faq">FAQ</a>
          <a href="{CALENDLY}" target="_blank" rel="noreferrer" class="button button-electric">
            <span>Book a free call</span>
            <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="square"/></svg>
          </a>
        </nav>
      </div>
    </header>"""


def footer(home: str) -> str:
    """Site footer. `home` is the root-relative path to index.html."""
    return f"""    <footer class="site-footer">
      <div class="container footer-grid">
        <div class="footer-brand">
          <a class="brand-lockup" href="{home}" aria-label="Turnkey AI">
            {BRAND_MARK}
            <div class="brand-words">
              <span class="brand-name">TURNKEY</span>
              <span class="brand-sub">AI</span>
            </div>
          </a>
          <p>Practical AI for service businesses. Built without the jargon, the long contracts, or the enterprise price tag.</p>
        </div>

        <div class="footer-col">
          <p class="foot-label">Explore</p>
          <a href="{home}#what-we-do">What we do</a>
          <a href="{ROOT}/industries/">Industries</a>
          <a href="{ROOT}/blog/">Blog</a>
          <a href="{home}#pricing">Pricing</a>
          <a href="{home}#faq">FAQ</a>
        </div>

        <div class="footer-col">
          <p class="foot-label">Talk to us</p>
          <a href="{CALENDLY}" target="_blank" rel="noreferrer">Book a free call</a>
          <a href="mailto:{EMAIL}">{EMAIL}</a>
          <span>Austin, Texas</span>
        </div>
      </div>

      <div class="footer-bar">
        <span>&copy; {YEAR} Turnkey AI</span>
        <span class="foot-status"><span class="status-dot"></span> Built for real businesses</span>
      </div>
    </footer>"""


def org_jsonld() -> str:
    """Organization JSON-LD — site-wide."""
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Turnkey AI",
        "url": f"{BASE_URL}/",
        "description": "Custom AI tools and automations for service businesses doing $1M-$5M in revenue.",
        "email": EMAIL,
        "founder": {"@type": "Person", "name": "Ricky West"},
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Austin",
            "addressRegion": "TX",
            "addressCountry": "US",
        },
        "areaServed": "US",
        "slogan": "AI for service businesses, without the headache.",
    }
    return json.dumps(data, indent=2)


# ----------------------------------------------------------------------------
# Tool-card icons (cycled by index) — reuse the home-page capability SVGs
# ----------------------------------------------------------------------------

TOOL_ICONS = [
    """<svg viewBox="0 0 48 48" aria-hidden="true">
          <circle cx="24" cy="24" r="3" fill="url(#tk-electric)"/>
          <circle cx="24" cy="24" r="10" fill="none" stroke="url(#tk-electric)" stroke-width="1.5" opacity="0.6"/>
          <circle cx="24" cy="24" r="18" fill="none" stroke="url(#tk-electric)" stroke-width="1" opacity="0.3"/>
          <circle cx="42" cy="24" r="2" fill="#7DE0FF"/><circle cx="6" cy="24" r="2" fill="#7DE0FF"/>
          <circle cx="24" cy="6" r="2" fill="#7DE0FF"/><circle cx="24" cy="42" r="2" fill="#7DE0FF"/>
        </svg>""",
    """<svg viewBox="0 0 48 48" aria-hidden="true">
          <rect x="8" y="14" width="32" height="4" rx="1" fill="url(#tk-electric)"/>
          <rect x="8" y="22" width="22" height="4" rx="1" fill="url(#tk-electric)" opacity="0.7"/>
          <rect x="8" y="30" width="28" height="4" rx="1" fill="url(#tk-electric)" opacity="0.4"/>
          <circle cx="38" cy="24" r="3" fill="#7DE0FF"/>
        </svg>""",
    """<svg viewBox="0 0 48 48" aria-hidden="true">
          <path d="M8 36 L18 22 L26 28 L40 10" fill="none" stroke="url(#tk-electric)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="8" cy="36" r="2.5" fill="#7DE0FF"/><circle cx="18" cy="22" r="2.5" fill="#7DE0FF"/>
          <circle cx="26" cy="28" r="2.5" fill="#7DE0FF"/><circle cx="40" cy="10" r="2.5" fill="#7DE0FF"/>
        </svg>""",
    """<svg viewBox="0 0 48 48" aria-hidden="true">
          <circle cx="24" cy="20" r="8" fill="none" stroke="url(#tk-electric)" stroke-width="2"/>
          <path d="M12 40 Q24 30 36 40" fill="none" stroke="url(#tk-electric)" stroke-width="2" stroke-linecap="round"/>
          <circle cx="24" cy="20" r="2" fill="#7DE0FF"/>
        </svg>""",
]


# ----------------------------------------------------------------------------
# Industry page renderer
# ----------------------------------------------------------------------------

def _impact_stat(impact: str) -> tuple[str, str]:
    """Pull a headline figure + label out of an impact sentence.

    Returns (value, label). Falls back to a generic pairing when no number
    is found, so every case row gets a clean mini-stat.
    """
    text = impact.replace("Representative result:", "").strip()
    # money amount, e.g. ~$11,000/month  or  $40k
    m = re.search(r"~?\$[\d,]+(?:\.\d+)?\s*(?:k|/month|/mo|/yr|a month|a year)?", text)
    if m:
        val = m.group(0).lstrip("~").strip()
        label = "monthly impact" if any(x in val for x in ("month", "mo")) else "recovered"
        val = val.replace("/month", "").replace("/mo", "").replace("/yr", "")
        return val + ("/mo" if label == "monthly impact" else ""), label
    # hours, e.g. ~6 hours a week / 8-10 hours
    m = re.search(r"~?\d+(?:[–-]\d+)?\s*(?:hrs?|hours?)", text)
    if m:
        num = re.search(r"\d+(?:[–-]\d+)?", m.group(0)).group(0)
        return num + " hrs", "reclaimed weekly"
    # percentage
    m = re.search(r"~?\d+%", text)
    if m:
        return m.group(0).lstrip("~"), "measured lift"
    # plain count, e.g. "+53 reviews"
    m = re.search(r"[+]?\d+", text)
    if m:
        return m.group(0), "the measured change"
    # no figure in the impact text — use a qualitative stat that does not
    # collide with the build-time / price columns next to it.
    return "Owner-led", "built with you, not at you"


def render_industry(ind: dict) -> str:
    slug = ind["slug"]
    name = ind["name"]
    home = f"{ROOT}/index.html"
    canonical = f"{BASE_URL}/industries/{slug}/"

    # --- drains list (the work that drains this trade's week) ---
    drains_html = "\n".join(
        f"""              <div class="who-row">
                <span class="who-check">
                  <svg viewBox="0 0 24 24" fill="none"><path d="M5 12l4 4L19 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </span>
                <div><h3>{esc(d)}</h3></div>
              </div>"""
        for d in ind["drains"]
    )

    # --- tool cards (footer micro-line keeps parity with the home cap-cards) ---
    CAP_FOOTS = [
        "Built on the tools you already run &mdash; you own it at launch.",
        "Live in 1&ndash;2 weeks, with 30 days of tuning included.",
        "A real person walks your team through it &mdash; no manual to read.",
        "Quietly pays for itself, then runs without you watching it.",
    ]
    tool_cards = []
    for i, t in enumerate(ind["tools"]):
        icon = TOOL_ICONS[i % len(TOOL_ICONS)]
        foot = CAP_FOOTS[i % len(CAP_FOOTS)]
        tool_cards.append(f"""            <article class="cap-card">
              <div class="cap-icon">{icon}</div>
              <p class="cap-tag">{esc(t['tag'])}</p>
              <h3>{esc(t['title'])}</h3>
              <p class="cap-body">{esc(t['body'])}</p>
              <p class="cap-foot"><span class="cap-foot-dot" aria-hidden="true"></span> {foot}</p>
            </article>""")
    tools_html = "\n".join(tool_cards)

    # --- case rows: headline derived from the matching tool, plus a mini-stat ---
    case_rows = []
    for i, c in enumerate(ind["cases"], 1):
        tool = ind["tools"][(i - 1) % len(ind["tools"])]
        stat_val, stat_label = _impact_stat(c["impact"])
        case_rows.append(f"""            <article class="system-row">
              <div class="system-meta">
                <span class="system-num">{i:02d}</span>
                <span class="system-meta-label">The situation</span>
                <span class="system-tag">{esc(c['context'])}</span>
                <span class="system-revenue">Representative example &mdash; not a named client</span>
              </div>
              <div class="system-body">
                <h3>{esc(tool['title'])}</h3>
                <div class="ba-flow">
                  <div class="ba-step ba-before">
                    <span class="ba-label">Before</span>
                    <p>{esc(c['before'])}</p>
                  </div>
                  <div class="ba-arrow" aria-hidden="true">&rarr;</div>
                  <div class="ba-step ba-after">
                    <span class="ba-label">After</span>
                    <p>{esc(c['after'])}</p>
                  </div>
                  <div class="ba-arrow" aria-hidden="true">&rarr;</div>
                  <div class="ba-step ba-impact">
                    <span class="ba-label">Impact</span>
                    <p>{esc(c['impact'])}</p>
                  </div>
                </div>
                <div class="system-stats">
                  <div><strong>{esc(stat_val)}</strong><span>{esc(stat_label)}</span></div>
                  <div><strong>2 wks</strong><span>typical build time</span></div>
                  <div><strong>From $1,500</strong><span>one-time, you own it</span></div>
                </div>
              </div>
            </article>""")
    cases_html = "\n".join(case_rows)

    # --- FAQ: trade-specific entries first, then two universal entries so
    #     every industry page carries a fuller, more reassuring FAQ block. ---
    UNIVERSAL_FAQ = [
        {"q": "What if AI isn't the right answer for my problem?",
         "a": "We'll tell you. Honestly — plenty of our first calls end with us saying "
              "“you don't need AI for that, you need a better process” or "
              "“this is a $200 Zapier zap, not a $5k build.” We make our money on "
              "great fits, not by selling everyone an automation. The 15-minute call is "
              "free either way."},
        {"q": "What happens if the tool breaks or makes a mistake?",
         "a": "Every build has approval gates wherever the stakes are real — sending a "
              "customer message, processing a payment, booking a job. The tool drafts, you "
              "approve. For the first 30 days after launch we monitor it daily and fix "
              "anything that drifts. After that you can keep us on retainer or take it fully "
              "in-house — your call."},
    ]
    all_faq = list(ind["faq"]) + UNIVERSAL_FAQ
    faq_items = []
    for i, f in enumerate(all_faq):
        open_attr = " open" if i == 0 else ""
        faq_items.append(f"""            <details class="faq-item"{open_attr}>
              <summary>
                <span>{esc(f['q'])}</span>
                <span class="faq-icon" aria-hidden="true">+</span>
              </summary>
              <div class="faq-answer">
                <p>{esc(f['a'])}</p>
              </div>
            </details>""")
    faq_html = "\n".join(faq_items)

    # --- JSON-LD: Service + BreadcrumbList + FAQPage ---
    service_ld = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": f"AI tools for {name} businesses",
        "serviceType": "Custom AI automation",
        "description": ind["meta_description"],
        "provider": {"@type": "Organization", "name": "Turnkey AI", "url": f"{BASE_URL}/"},
        "areaServed": "US",
        "audience": {"@type": "Audience", "audienceType": ind["name_plural"]},
        "url": canonical,
        "offers": {
            "@type": "Offer",
            "priceCurrency": "USD",
            "price": "1500",
            "description": "Custom AI tool builds for service businesses, starting at $1,500.",
        },
    }
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Industries", "item": f"{BASE_URL}/industries/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ],
    }
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f["q"],
                "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
            }
            for f in all_faq
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(ind['title'])}</title>
  <meta name="description" content="{esc(ind['meta_description'])}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(ind['title'])}">
  <meta property="og:description" content="{esc(ind['meta_description'])}">
  <meta property="og:url" content="{canonical}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{ROOT}/styles.css">
  <script type="application/ld+json">
{org_jsonld()}
  </script>
  <script type="application/ld+json">
{json.dumps(service_ld, indent=2)}
  </script>
  <script type="application/ld+json">
{json.dumps(breadcrumb_ld, indent=2)}
  </script>
  <script type="application/ld+json">
{json.dumps(faq_ld, indent=2)}
  </script>
</head>
<body>

{GRAD_DEFS}

  <div class="site-shell">

    <div class="pulse-field" aria-hidden="true">
      <svg class="wave-svg wave-svg--top" viewBox="0 0 1600 400" preserveAspectRatio="none">
        <g class="wave-dots"></g>
      </svg>
      <svg class="wave-svg wave-svg--bottom" viewBox="0 0 1600 400" preserveAspectRatio="none">
        <g class="wave-dots"></g>
      </svg>
      <div class="grid-overlay"></div>
    </div>

{header(home)}

    <main>

      <!-- BREADCRUMB -->
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <div class="container">
          <a href="{home}">Home</a>
          <span aria-hidden="true">/</span>
          <a href="{ROOT}/industries/">Industries</a>
          <span aria-hidden="true">/</span>
          <span aria-current="page">{esc(name)}</span>
        </div>
      </nav>

      <!-- HERO -->
      <section class="hero industry-hero">
        <div class="container">
          <div class="hero-copy reveal">
            <p class="kicker"><span class="status-dot"></span> Built for {esc(ind['name_plural'])} doing $1M&ndash;$5M</p>
            <h1>{esc(ind['h1_lead'])} <span class="grad-text">{esc(ind['h1_grad'])}</span></h1>
            <p class="lede lede-lead">{esc(ind['hero_lede'])}</p>
            <div class="hero-actions">
              <a href="{CALENDLY}" target="_blank" rel="noreferrer" class="button button-electric button-lg">
                <span>Book a free 15-min call</span>
                <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="square"/></svg>
              </a>
              <a href="#tools" class="button button-ghost">See the tools</a>
            </div>
            <div class="fact-row">
              <div><strong>2 wks</strong><span>from first call to live</span></div>
              <div><strong>$1,500</strong><span>starting price</span></div>
              <div><strong>90-day</strong><span>earns-its-keep promise</span></div>
              <div><strong>0</strong><span>long-term contracts</span></div>
            </div>
            <p class="hero-note">Built in two weeks. $1,500 to $6,000. No retainers, no long contracts &mdash; and a real person who knows your world.</p>
          </div>
        </div>
      </section>

      <!-- THE WORK THAT DRAINS YOUR WEEK -->
      <section class="section section-position">
        <div class="container">
          <div class="who-grid reveal">
            <div class="who-copy">
              <p class="kicker">Where the time goes</p>
              <h2>The work quietly eating <span class="grad-text">your {esc(name)} week.</span></h2>
              <p>You didn't get into this business to live on the phone or write quotes at midnight. These are the things we hear about on almost every first call with an owner in {esc(name)}.</p>
              <p class="who-secondary">If two or three of these sound familiar, there's a tool worth building.</p>
            </div>
            <div class="who-list">
{drains_html}
            </div>
          </div>
        </div>
      </section>

      <!-- AI TOOLS FOR THIS TRADE -->
      <section class="section" id="tools">
        <div class="container">
          <div class="section-head reveal">
            <p class="kicker">What we'd build for you</p>
            <h2>Practical AI tools, <span class="grad-text">made for {esc(name)}.</span></h2>
            <p>Not a chatbot with a monthly fee. Small, reliable tools that do a specific job inside the workflow you already run &mdash; so your team is free for the work that grows the business.</p>
          </div>
          <div class="capability-grid reveal">
{tools_html}
          </div>
        </div>
      </section>

      <!-- BEFORE / AFTER CASES -->
      <section class="section section-contrast" style="padding:80px 0;">
        <div class="container">
          <div class="section-head reveal">
            <p class="kicker">What this looks like</p>
            <h2>Representative results <span class="grad-text">for {esc(ind['name_plural'])}.</span></h2>
            <p>These are illustrative examples of the kind of change these tools make &mdash; not named clients. The dollar and time figures are realistic, plain-English estimates of typical impact.</p>
          </div>
          <div class="systems-list reveal">
{cases_html}
          </div>
        </div>
      </section>

      <!-- MID-PAGE CTA BAND -->
      <section class="cta-band">
        <div class="container">
          <div class="cta-band-inner reveal">
            <div class="cta-band-copy">
              <h2>See your {esc(name)} business in any of this?</h2>
              <p>Book a free 15-minute call. We'll talk through your specific situation &mdash; no deck, no pressure.</p>
            </div>
            <a href="{CALENDLY}" target="_blank" rel="noreferrer" class="button button-electric button-lg">
              <span>Book a free call</span>
              <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="square"/></svg>
            </a>
          </div>
        </div>
      </section>

      <!-- HOW IT WORKS -->
      <section class="section" style="padding-top:48px;">
        <div class="container">
          <div class="section-head reveal">
            <p class="kicker">How it works</p>
            <h2>From first call to <span class="grad-text">working tool</span> in two weeks.</h2>
            <p>No long discovery process, no 80-page proposals. We talk, we agree on a small first project, and we build it.</p>
          </div>
          <div class="process-rail reveal">
            <div class="process-step">
              <div class="step-marker"><span>01</span><div class="step-line"></div></div>
              <h3>We talk</h3>
              <p>A free 15-minute call. You tell us what's eating your {esc(name)} week. We tell you honestly whether AI is the right answer.</p>
              <p class="step-time">Day 1 &middot; free</p>
            </div>
            <div class="process-step">
              <div class="step-marker"><span>02</span><div class="step-line"></div></div>
              <h3>We scope it</h3>
              <p>If there's a fit, you get a one-page proposal: what we'll build, what it costs, when it's done. No deck, no upsell.</p>
              <p class="step-time">Days 2&ndash;3</p>
            </div>
            <div class="process-step">
              <div class="step-marker"><span>03</span><div class="step-line"></div></div>
              <h3>We build it</h3>
              <p>You'll see progress every few days. We test it on your real data and walk you through it in plain English.</p>
              <p class="step-time">Days 4&ndash;12</p>
            </div>
            <div class="process-step">
              <div class="step-marker"><span>04</span><div class="step-line"></div></div>
              <h3>It runs</h3>
              <p>We hand you the keys and stay close for 30 days while it gets real-world testing. Then you decide what's next.</p>
              <p class="step-time">Day 13 &rarr; onward</p>
            </div>
          </div>
        </div>
      </section>

      <!-- PRICING RECAP -->
      <section class="section section-pricing">
        <div class="container">
          <div class="section-head reveal">
            <p class="kicker">Pricing</p>
            <h2>Simple, project-based pricing. <span class="grad-text">No surprises.</span></h2>
            <p>You pay once, you own the tool, and we stay on for a month to make sure it runs the way you need it to.</p>
          </div>
          <div class="pricing-grid reveal">
            <article class="price-card">
              <p class="price-tag">Start small</p>
              <h3>One Quick Win</h3>
              <p class="price-amount"><span class="price-from">from</span> $1,500</p>
              <p class="price-blurb">Pick the one thing draining your week. We build a focused tool that handles it end-to-end.</p>
              <ul>
                <li>One workflow automated end-to-end</li>
                <li>Built and live in 1&ndash;2 weeks</li>
                <li>30 days of post-launch tuning included</li>
                <li>You own everything we build</li>
              </ul>
            </article>
            <article class="price-card price-card-featured">
              <p class="price-tag">Most owners start here</p>
              <h3>The Operating Bundle</h3>
              <p class="price-amount"><span class="price-from">from</span> $4,500</p>
              <p class="price-blurb">A connected set of tools &mdash; usually lead follow-up, a daily owner brief, and one back-office automation.</p>
              <ul>
                <li>2&ndash;3 workflows automated and connected</li>
                <li>Built and live in 2&ndash;3 weeks</li>
                <li>60 days of post-launch tuning</li>
                <li>Team onboarding + walkthrough video</li>
              </ul>
            </article>
            <article class="price-card">
              <p class="price-tag">When you're ready</p>
              <h3>Ongoing Partner</h3>
              <p class="price-amount"><span class="price-from">from</span> $750<span class="price-period">/mo</span></p>
              <p class="price-blurb">We keep your tools running, fix anything that breaks, and add new automations as you grow.</p>
              <ul>
                <li>We monitor and maintain everything</li>
                <li>One new automation per quarter included</li>
                <li>Priority response if anything breaks</li>
                <li>Cancel anytime &mdash; no contracts</li>
              </ul>
            </article>
          </div>
          <p class="price-footnote">Our promise: if the first build doesn't earn its keep within 90 days of going live, we refund the difference. No fine print.</p>
        </div>
      </section>

      <!-- FAQ -->
      <section class="section section-faq">
        <div class="container">
          <div class="section-head reveal">
            <p class="kicker">Common questions</p>
            <h2>What {esc(name)} owners <span class="grad-text">ask us.</span></h2>
          </div>
          <div class="faq-list reveal">
{faq_html}
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="section section-cta">
        <div class="container">
          <div class="cta-card reveal">
            <div class="cta-pulse" aria-hidden="true">
              <svg viewBox="0 0 600 200" preserveAspectRatio="none">
                <path class="pulse-path" d="M0 100 L100 100 L120 60 L140 140 L160 80 L180 120 L200 100 L320 100 L340 40 L360 160 L380 70 L400 130 L420 100 L600 100" fill="none" stroke="url(#tk-electric-h)" stroke-width="2"/>
              </svg>
            </div>
            <div class="cta-grid" style="grid-template-columns:1fr;">
              <div class="cta-left">
                <p class="kicker">Book a free call</p>
                <h2>Let's find the one tool worth building <span class="grad-text">for your {esc(name)} business.</span></h2>
                <p class="cta-lede">15 minutes. No deck, no pressure. We'll listen, ask the right questions, and tell you honestly whether AI can help &mdash; and what a first project would look like.</p>
                <ul class="cta-list">
                  <li>You'll talk to Ricky, our founder &mdash; not a salesperson</li>
                  <li>If we can't help, we'll tell you in the first 10 minutes</li>
                  <li>If we can, you'll leave with a clear next step</li>
                </ul>
                <a href="{CALENDLY}" target="_blank" rel="noreferrer" class="button button-electric button-lg cta-button">
                  <span>Pick a time on Calendly</span>
                  <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="square"/></svg>
                </a>
                <p class="cta-fineprint">Or email Ricky directly at <a href="mailto:{EMAIL}">{EMAIL}</a></p>
              </div>
            </div>
          </div>
        </div>
      </section>

    </main>

{footer(home)}

  </div>

  <script src="{ROOT}/site.js"></script>
</body>
</html>
"""


# ----------------------------------------------------------------------------
# Industry hub page renderer
# ----------------------------------------------------------------------------

def render_hub(industries: list[dict]) -> str:
    home = f"{ROOT}/index.html"
    canonical = f"{BASE_URL}/industries/"

    # group industries
    by_group: dict[str, list[dict]] = {g: [] for g in GROUP_ORDER}
    for ind in industries:
        by_group.setdefault(ind["group"], []).append(ind)

    group_blocks = []
    for g in GROUP_ORDER:
        items = sorted(by_group.get(g, []), key=lambda x: x["name"])
        if not items:
            continue
        cards = []
        for ind in items:
            cards.append(f"""            <a class="industry-card" href="{ROOT}/industries/{ind['slug']}/">
              <span class="industry-card-name">{esc(ind['name'])}</span>
              <span class="industry-card-arrow" aria-hidden="true">
                <svg viewBox="0 0 16 16"><path d="M2 8h10M8 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="square"/></svg>
              </span>
            </a>""")
        group_blocks.append(f"""        <div class="industry-group reveal">
          <h2 class="industry-group-title">{esc(g)}</h2>
          <div class="industry-card-grid">
{chr(10).join(cards)}
          </div>
        </div>""")
    groups_html = "\n".join(group_blocks)

    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Industries", "item": canonical},
        ],
    }
    item_list_ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Industries Turnkey AI serves",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": f"AI tools for {ind['name']} businesses",
                "url": f"{BASE_URL}/industries/{ind['slug']}/",
            }
            for i, ind in enumerate(sorted(industries, key=lambda x: x["name"]))
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Industries We Build AI Tools For | Turnkey AI</title>
  <meta name="description" content="Turnkey AI builds custom AI tools for 30+ service trades — HVAC, plumbing, roofing, salons, auto repair, and more. Built in two weeks from $1,500.">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="Industries We Build AI Tools For | Turnkey AI">
  <meta property="og:description" content="Custom AI tools for 30+ service trades. Built in two weeks, starting at $1,500.">
  <meta property="og:url" content="{canonical}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{ROOT}/styles.css">
  <script type="application/ld+json">
{org_jsonld()}
  </script>
  <script type="application/ld+json">
{json.dumps(breadcrumb_ld, indent=2)}
  </script>
  <script type="application/ld+json">
{json.dumps(item_list_ld, indent=2)}
  </script>
</head>
<body>

{GRAD_DEFS}

  <div class="site-shell">

    <div class="pulse-field" aria-hidden="true">
      <svg class="wave-svg wave-svg--top" viewBox="0 0 1600 400" preserveAspectRatio="none">
        <g class="wave-dots"></g>
      </svg>
      <svg class="wave-svg wave-svg--bottom" viewBox="0 0 1600 400" preserveAspectRatio="none">
        <g class="wave-dots"></g>
      </svg>
      <div class="grid-overlay"></div>
    </div>

{header(home)}

    <main>

      <nav class="breadcrumb" aria-label="Breadcrumb">
        <div class="container">
          <a href="{home}">Home</a>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Industries</span>
        </div>
      </nav>

      <section class="hero industry-hero">
        <div class="container">
          <div class="hero-copy reveal">
            <p class="kicker"><span class="status-dot"></span> 30 trades &mdash; and counting</p>
            <h1>AI tools, built for <span class="grad-text">the trade you actually run.</span></h1>
            <p class="lede lede-lead">We've built tools for service businesses across more than 30 trades. The work that drains an HVAC week is not the work that drains a salon week &mdash; so we don't pretend otherwise. Find your trade below.</p>
            <div class="hero-actions">
              <a href="{CALENDLY}" target="_blank" rel="noreferrer" class="button button-electric button-lg">
                <span>Book a free 15-min call</span>
                <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="square"/></svg>
              </a>
            </div>
            <p class="hero-note">Don't see your trade? It doesn't matter much &mdash; the approach is the same. <a href="{CALENDLY}" target="_blank" rel="noreferrer" style="color:var(--electric);text-decoration:underline;">Book a call</a> and we'll talk about your business specifically.</p>
          </div>
        </div>
      </section>

      <section class="section section-position" style="padding-top:40px;">
        <div class="container industry-hub">
{groups_html}
        </div>
      </section>

      <section class="cta-band">
        <div class="container">
          <div class="cta-band-inner reveal">
            <div class="cta-band-copy">
              <h2>See your trade on the list?</h2>
              <p>Book a free 15-minute call. We'll talk about your specific situation &mdash; no deck, no pressure.</p>
            </div>
            <a href="{CALENDLY}" target="_blank" rel="noreferrer" class="button button-electric button-lg">
              <span>Book a free call</span>
              <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="square"/></svg>
            </a>
          </div>
        </div>
      </section>

    </main>

{footer(home)}

  </div>

  <script src="{ROOT}/site.js"></script>
</body>
</html>
"""


# ----------------------------------------------------------------------------
# Blog hub page renderer (empty-state — SEO engine populates blog/<slug>/ later)
# ----------------------------------------------------------------------------

def render_blog_index() -> str:
    home = f"{ROOT}/index.html"
    canonical = f"{BASE_URL}/blog/"
    blog_ld = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Turnkey AI Blog",
        "description": "Practical, plain-English writing on putting AI to work in a service business.",
        "url": canonical,
        "publisher": {"@type": "Organization", "name": "Turnkey AI"},
    }
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": canonical},
        ],
    }
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog | Turnkey AI</title>
  <meta name="description" content="Practical, plain-English writing on putting AI to work in a service business. New articles from the Turnkey AI team coming soon.">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="Blog | Turnkey AI">
  <meta property="og:description" content="Practical, plain-English writing on putting AI to work in a service business.">
  <meta property="og:url" content="{canonical}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{ROOT}/styles.css">
  <link rel="stylesheet" href="{ROOT}/blog/blog-styles.css">
  <script type="application/ld+json">
{org_jsonld()}
  </script>
  <script type="application/ld+json">
{json.dumps(blog_ld, indent=2)}
  </script>
  <script type="application/ld+json">
{json.dumps(breadcrumb_ld, indent=2)}
  </script>
</head>
<body>

{GRAD_DEFS}

  <div class="site-shell">

    <div class="pulse-field" aria-hidden="true">
      <svg class="wave-svg wave-svg--top" viewBox="0 0 1600 400" preserveAspectRatio="none">
        <g class="wave-dots"></g>
      </svg>
      <svg class="wave-svg wave-svg--bottom" viewBox="0 0 1600 400" preserveAspectRatio="none">
        <g class="wave-dots"></g>
      </svg>
      <div class="grid-overlay"></div>
    </div>

{header(home)}

    <main>

      <nav class="breadcrumb" aria-label="Breadcrumb">
        <div class="container">
          <a href="{home}">Home</a>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Blog</span>
        </div>
      </nav>

      <section class="hero industry-hero">
        <div class="container">
          <div class="hero-copy reveal">
            <p class="kicker"><span class="status-dot"></span> The Turnkey AI blog</p>
            <h1>Plain-English writing on <span class="grad-text">AI for real businesses.</span></h1>
            <p class="lede lede-lead">No hype, no jargon. Practical notes on where AI actually helps a service business &mdash; and where it honestly doesn't &mdash; from the team that builds the tools.</p>
          </div>
        </div>
      </section>

      <section class="section section-position" style="padding-top:32px;">
        <div class="container">
          <!-- ARTICLE LIST: the SEO content engine publishes articles at
               /blog/<slug>/index.html and adds <article class="post-card"> entries here. -->
          <div class="blog-list reveal" id="blog-list">

            <div class="blog-empty">
              <div class="blog-empty-mark" aria-hidden="true">
                <svg viewBox="0 0 48 48">
                  <rect x="8" y="10" width="32" height="4" rx="1" fill="url(#tk-electric)"/>
                  <rect x="8" y="20" width="24" height="4" rx="1" fill="url(#tk-electric)" opacity="0.6"/>
                  <rect x="8" y="30" width="28" height="4" rx="1" fill="url(#tk-electric)" opacity="0.35"/>
                </svg>
              </div>
              <h2>Articles coming soon</h2>
              <p>We're putting the first set of articles together now &mdash; practical, no-nonsense pieces on getting real value from AI in a service business. Check back shortly.</p>
              <p class="blog-empty-cta">In the meantime, the fastest way to get a straight answer about your business is a quick call.</p>
              <a href="{CALENDLY}" target="_blank" rel="noreferrer" class="button button-electric button-lg">
                <span>Book a free 15-min call</span>
                <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8h10M8 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="square"/></svg>
              </a>
            </div>

          </div>
        </div>
      </section>

    </main>

{footer(home)}

  </div>

  <script src="{ROOT}/site.js"></script>
</body>
</html>
"""


BLOG_CSS = """/* ============================================================
   TURNKEY AI — Blog styles
   Layered on top of styles.css. Used by /blog/ and /blog/<slug>/.
   ============================================================ */

/* ---- Blog list / empty state ---- */
.blog-list {
  max-width: 880px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.blog-empty {
  text-align: center;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 64px 48px 56px;
  box-shadow: var(--shadow-card);
}
.blog-empty-mark {
  width: 56px;
  height: 56px;
  margin: 0 auto 24px;
  padding: 12px;
  background: var(--icy-soft);
  border: 1px solid rgba(0, 82, 255, 0.14);
  border-radius: 12px;
}
.blog-empty-mark svg { width: 100%; height: 100%; }
.blog-empty h2 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text);
  margin-bottom: 14px;
}
.blog-empty p {
  font-size: 16px;
  color: var(--text-soft);
  line-height: 1.6;
  max-width: 540px;
  margin: 0 auto 12px;
}
.blog-empty-cta {
  margin-top: 8px !important;
  margin-bottom: 24px !important;
  font-weight: 500;
  color: var(--text) !important;
}

/* ---- Post cards (the SEO engine renders these once articles exist) ---- */
.post-card {
  display: block;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 28px 30px;
  box-shadow: var(--shadow-card);
  transition: all 280ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
.post-card:hover {
  transform: translateY(-3px);
  border-color: rgba(0, 82, 255, 0.22);
  box-shadow: 0 1px 2px rgba(10, 18, 32, 0.04), 0 24px 60px rgba(0, 82, 255, 0.14);
}
.post-card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-mute);
  margin-bottom: 12px;
}
.post-card-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--electric);
}
.post-card h2 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.015em;
  line-height: 1.25;
  color: var(--text);
  margin-bottom: 10px;
}
.post-card p {
  font-size: 15px;
  color: var(--text-soft);
  line-height: 1.6;
}

/* ---- Article body (for /blog/<slug>/index.html) ---- */
.article {
  max-width: 760px;
  margin: 0 auto;
}
.article-header {
  margin-bottom: 40px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--line);
}
.article-header h1 {
  font-size: clamp(32px, 4.4vw, 48px);
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.1;
  color: var(--text);
  margin-bottom: 18px;
}
.article-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-mute);
}
.article-body { font-size: 17px; line-height: 1.72; color: var(--text-soft); }
.article-body h2 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.018em;
  color: var(--text);
  margin: 40px 0 16px;
}
.article-body h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin: 28px 0 12px;
}
.article-body p { margin-bottom: 18px; }
.article-body ul, .article-body ol { margin: 0 0 18px 22px; }
.article-body li { margin-bottom: 8px; }
.article-body a {
  color: var(--electric);
  text-decoration: underline;
  text-decoration-color: rgba(0, 82, 255, 0.35);
}
.article-body a:hover { text-decoration-color: var(--electric); }
.article-body blockquote {
  border-left: 3px solid var(--electric);
  background: var(--icy-soft);
  padding: 16px 22px;
  border-radius: 0 8px 8px 0;
  margin: 0 0 18px;
  color: var(--text);
}

@media (max-width: 720px) {
  .blog-empty { padding: 48px 24px 40px; }
}
"""


# Industry-page specific styling, appended to styles.css via a separate block
# We inject it through styles.css — but to avoid editing the big file, we add a
# small <style> hook? No: cleaner to append a dedicated block to styles.css once.
EXTRA_CSS_MARKER = "/* === INDUSTRY-BUILDER GENERATED STYLES === */"

EXTRA_CSS = EXTRA_CSS_MARKER + """
/* Breadcrumb + industry/hub/blog page chrome — appended by build_industries.py */
.breadcrumb {
  position: relative;
  z-index: 1;
  padding: 20px 0 0;
}
.breadcrumb .container {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-mute);
  flex-wrap: wrap;
}
.breadcrumb a { color: var(--text-soft); transition: color 180ms ease; }
.breadcrumb a:hover { color: var(--electric); }
.breadcrumb span[aria-current] { color: var(--electric); font-weight: 600; }
.breadcrumb span[aria-hidden] { color: var(--text-faint); }

.industry-hero { padding: 56px 0 64px; }
.industry-hero .hero-copy { max-width: 880px; }
/* Industry hero fact-row sits a touch tighter than the home hero */
.industry-hero .fact-row { margin-top: 8px; margin-bottom: 22px; }

/* Drains rows on industry pages use an h3-weight statement (no body copy) */
.industry-hero ~ .section-position .who-row { align-items: center; }
.section-position .who-row h3 {
  font-size: 16.5px;
  font-weight: 600;
  letter-spacing: -0.005em;
  line-height: 1.5;
  color: var(--text);
  margin-bottom: 0;
}

/* Industry case meta column — a labelled "situation" block so the
   left rail reads as intentional, not empty whitespace. */
.system-meta-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-mute);
}
.systems-list .system-row .system-tag {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  color: var(--text);
}
.systems-list .system-row .system-revenue {
  font-size: 12px;
  color: var(--text-mute);
  font-weight: 500;
  letter-spacing: 0;
}

/* Tool-card footer micro-line — parity with the home cap-card list */
.cap-foot {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-mute);
  line-height: 1.45;
}
.cap-foot-dot {
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--electric);
}

/* Industry hub — grouped card grid */
.industry-hub {
  display: flex;
  flex-direction: column;
  gap: 56px;
}
.industry-group-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.015em;
  color: var(--text);
  margin-bottom: 22px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}
.industry-card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.industry-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 20px 22px;
  box-shadow: var(--shadow-card);
  transition: all 240ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
.industry-card:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 82, 255, 0.25);
  box-shadow: 0 1px 2px rgba(10, 18, 32, 0.04), 0 16px 40px rgba(0, 82, 255, 0.12);
}
.industry-card-name {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.005em;
  color: var(--text);
}
.industry-card:hover .industry-card-name { color: var(--electric); }
.industry-card-arrow {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: var(--icy-soft);
  border: 1px solid rgba(0, 82, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--electric);
  transition: transform 220ms ease;
}
.industry-card:hover .industry-card-arrow { transform: translateX(3px); }
.industry-card-arrow svg { width: 14px; height: 14px; }

@media (max-width: 1100px) {
  .industry-card-grid { grid-template-columns: repeat(2, 1fr); }
  /* Industry case rows carry a 240px meta sidebar — the 3-col before/after
     /impact flow gets too tight below 1100px, so stack it here (earlier
     than the home page's 720px breakpoint, which has no sidebar). */
  .systems-list .system-row .ba-flow {
    grid-template-columns: 1fr;
  }
  .systems-list .system-row .ba-arrow { transform: rotate(90deg); padding: 4px 0; }
}
@media (max-width: 720px) {
  .industry-card-grid { grid-template-columns: 1fr; }
  .industry-hero { padding: 40px 0 48px; }
}
"""


def ensure_extra_css() -> None:
    """Append industry-builder CSS to styles.css once (idempotent)."""
    css_path = SITE / "styles.css"
    text = css_path.read_text(encoding="utf-8")
    if EXTRA_CSS_MARKER in text:
        # replace existing block (everything from the marker to EOF)
        text = text[: text.index(EXTRA_CSS_MARKER)].rstrip() + "\n\n"
    text = text.rstrip() + "\n\n" + EXTRA_CSS + "\n"
    css_path.write_text(text, encoding="utf-8")
    print("  styles.css : industry-builder CSS block in place")


def patch_home_nav() -> None:
    """Add Industries + Blog links to the home index.html nav + footer (idempotent)."""
    home_path = SITE / "index.html"
    text = home_path.read_text(encoding="utf-8")
    changed = False

    # --- desktop nav: insert Industries after 'What we do', Blog after 'Pricing' ---
    if 'href="/turnkey-ai-site/industries/"' not in text and 'href="industries/"' not in text:
        nav_old = '          <a href="#what-we-do">What we do</a>\n          <a href="#examples">Examples</a>\n          <a href="#pricing">Pricing</a>\n          <a href="#faq">FAQ</a>'
        nav_new = (f'          <a href="#what-we-do">What we do</a>\n'
                   f'          <a href="{ROOT}/industries/">Industries</a>\n'
                   f'          <a href="#examples">Examples</a>\n'
                   f'          <a href="#pricing">Pricing</a>\n'
                   f'          <a href="{ROOT}/blog/">Blog</a>\n'
                   f'          <a href="#faq">FAQ</a>')
        if nav_old in text:
            text = text.replace(nav_old, nav_new, 1)
            changed = True

    # --- footer Explore column: add Industries + Blog ---
    foot_old = ('          <p class="foot-label">Explore</p>\n'
                '          <a href="#what-we-do">What we do</a>\n'
                '          <a href="#examples">Examples</a>\n'
                '          <a href="#pricing">Pricing</a>\n'
                '          <a href="#faq">FAQ</a>\n'
                '          <a href="#founder">From the founder</a>')
    if foot_old in text:
        foot_new = ('          <p class="foot-label">Explore</p>\n'
                    '          <a href="#what-we-do">What we do</a>\n'
                    f'          <a href="{ROOT}/industries/">Industries</a>\n'
                    '          <a href="#examples">Examples</a>\n'
                    '          <a href="#pricing">Pricing</a>\n'
                    f'          <a href="{ROOT}/blog/">Blog</a>\n'
                    '          <a href="#faq">FAQ</a>')
        text = text.replace(foot_old, foot_new, 1)
        changed = True

    # --- add Organization JSON-LD to home if missing ---
    if 'application/ld+json' not in text:
        ld_block = f'  <script type="application/ld+json">\n{org_jsonld()}\n  </script>\n'
        text = text.replace("</head>", ld_block + "</head>", 1)
        changed = True

    if changed:
        home_path.write_text(text, encoding="utf-8")
        print("  index.html : home nav + footer + JSON-LD patched")
    else:
        print("  index.html : already patched (no change)")


def write_sitemap(industries: list[dict]) -> None:
    today = date.today().isoformat()
    urls = [f"{BASE_URL}/", f"{BASE_URL}/industries/", f"{BASE_URL}/blog/"]
    urls += [f"{BASE_URL}/industries/{i['slug']}/" for i in sorted(industries, key=lambda x: x["slug"])]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        pr = "1.0" if u == f"{BASE_URL}/" else ("0.8" if u.endswith("/industries/") else "0.7")
        lines += ["  <url>",
                  f"    <loc>{u}</loc>",
                  f"    <lastmod>{today}</lastmod>",
                  f"    <priority>{pr}</priority>",
                  "  </url>"]
    lines.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  sitemap.xml : {len(urls)} URLs")


def write_robots() -> None:
    txt = ("User-agent: *\n"
           "Allow: /\n\n"
           f"Sitemap: {BASE_URL}/sitemap.xml\n")
    (SITE / "robots.txt").write_text(txt, encoding="utf-8")
    print("  robots.txt : written")


def main() -> None:
    print(f"Turnkey AI industry builder")
    print(f"  base URL : {BASE_URL}")
    print(f"  root prefix : '{ROOT}'\n")

    # load industry data
    files = sorted(DATA.glob("*.json"))
    industries = [json.loads(p.read_text(encoding="utf-8")) for p in files]
    if len(industries) != 30:
        raise SystemExit(f"Expected 30 industry JSON files, found {len(industries)}. "
                         f"Run seed_industries.py first.")

    # 1) industry styles into styles.css
    ensure_extra_css()

    # 2) 30 industry pages
    for ind in industries:
        out = SITE / "industries" / ind["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_industry(ind), encoding="utf-8")
    print(f"  industries/ : {len(industries)} pages")

    # 3) industry hub
    (SITE / "industries" / "index.html").write_text(render_hub(industries), encoding="utf-8")
    print("  industries/index.html : hub page")

    # 4) blog hub + styles
    (SITE / "blog").mkdir(parents=True, exist_ok=True)
    (SITE / "blog" / "blog-styles.css").write_text(BLOG_CSS, encoding="utf-8")
    (SITE / "blog" / "index.html").write_text(render_blog_index(), encoding="utf-8")
    print("  blog/ : index.html + blog-styles.css")

    # 5) sitemap + robots
    write_sitemap(industries)
    write_robots()

    # 6) patch home
    patch_home_nav()

    total = len(industries) + 1
    print(f"\nDone. {total} pages generated ({len(industries)} industry + 1 hub) + blog hub.")


if __name__ == "__main__":
    main()
