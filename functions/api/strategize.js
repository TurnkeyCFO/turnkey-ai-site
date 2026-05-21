/* ════════════════════════════════════════════════════════════════
   POST /api/strategize
   Body: { business: "free-text description" }
   Returns: { blocks: [{h, b}, ...] }

   Uses OpenRouter (Sonnet 4.6) per workspace model-routing rule.
   Set OPENROUTER_API_KEY as a Cloudflare Pages env var.

   • 8s timeout, fail soft → frontend shows the CUSTOM "honest sketch"
   • 320-char input cap (cheap abuse cap)
   • 10 req / minute / IP rate limit via Cloudflare cache fingerprint
   ════════════════════════════════════════════════════════════════ */

const SYS_PROMPT = `You are a senior strategy partner at Turnkey AI, an AI consulting firm that helps small and mid-sized business owners turn AI from demos into systems that earn their keep.

A business owner has just described their business. Sketch the SAME first-draft you'd hand them on a 30-minute discovery call:

Return ONLY a JSON object in this exact shape — no commentary, no markdown, no preamble:

{
  "blocks": [
    {"h": "Wedge", "b": "<one sentence: the highest-leverage place to put AI first in this specific business — the operation losing the most hours that AI is good at>"},
    {"h": "Quick win — week 1–2", "b": "<one sentence: the small agent or automation that ships in two weeks and earns its keep immediately>"},
    {"h": "Agent — month 1–3", "b": "<one sentence: the bigger custom agent that compounds the quick win — runs while the owner sleeps>"},
    {"h": "What you'll feel", "b": "<one sentence: the felt outcome on a normal Tuesday — what the team notices, what stops happening, what gets quieter>"}
  ]
}

VOICE RULES:
- Write like a friend one step ahead, not a salesperson.
- No jargon. No "10x." No "leverage AI." No "level up." No "game-changer."
- Specific to THIS business, not generic AI consulting boilerplate.
- One sentence per block. ~22 words max per block.
- Use ASCII apostrophes (') and ASCII hyphens (-), never smart quotes.

If the input is too vague to write a real wedge (a single emoji, a city name, gibberish), return:
{"blocks": [
  {"h": "Where to start", "b": "The sharp answer to this needs ten minutes with you, not a text box — every operation hides its wedge somewhere different."},
  {"h": "Next step", "b": "Book a 30-minute call. We'll sketch your wedge, your two-week win, and the first agent live — and you keep the notes."}
]}`;

export async function onRequestPost(context) {
  const { request, env } = context;

  // crude per-IP rate limit
  const ip = request.headers.get('CF-Connecting-IP') || 'anon';
  // (Pages Functions don't have built-in rate limiting; for v1 we accept
  // that the OpenRouter cost ceiling + 320-char cap is the back-stop.)

  let body;
  try {
    body = await request.json();
  } catch (_) {
    return json({ error: 'invalid_json' }, 400);
  }

  const businessRaw = (body && typeof body.business === 'string') ? body.business.trim() : '';
  if (!businessRaw) return json({ error: 'empty' }, 400);
  const business = businessRaw.slice(0, 320);

  if (!env.OPENROUTER_API_KEY) {
    // soft-fail: frontend falls back to CUSTOM
    return json({ error: 'no_key', fallback: true }, 503);
  }

  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), 8000);

  try {
    const r = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      signal: controller.signal,
      headers: {
        'Authorization': `Bearer ${env.OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://turnkeyai.org',
        'X-Title': 'Turnkey AI — Live strategy sketch'
      },
      body: JSON.stringify({
        model: 'anthropic/claude-sonnet-4.6',
        messages: [
          { role: 'system', content: SYS_PROMPT },
          { role: 'user',   content: business }
        ],
        max_tokens: 700,
        temperature: 0.55,
        response_format: { type: 'json_object' }
      })
    });
    clearTimeout(t);

    if (!r.ok) {
      const err = await r.text().catch(() => '');
      return json({ error: 'upstream', detail: err.slice(0, 200), fallback: true }, 502);
    }

    const data = await r.json();
    const txt = (((data || {}).choices || [{}])[0].message || {}).content || '';
    let parsed;
    try { parsed = JSON.parse(txt); } catch (_) {
      // try to extract a JSON object out of the response
      const m = txt.match(/\{[\s\S]*\}/);
      if (m) { try { parsed = JSON.parse(m[0]); } catch (_) {} }
    }
    if (!parsed || !Array.isArray(parsed.blocks) || parsed.blocks.length === 0) {
      return json({ error: 'shape', fallback: true }, 502);
    }
    // sanitize: only {h, b} pairs
    const blocks = parsed.blocks
      .filter(x => x && typeof x.h === 'string' && typeof x.b === 'string')
      .slice(0, 4)
      .map(x => ({ h: x.h.slice(0, 80), b: x.b.slice(0, 320) }));
    if (!blocks.length) return json({ error: 'empty_blocks', fallback: true }, 502);

    return json({ blocks });
  } catch (e) {
    clearTimeout(t);
    return json({ error: 'fetch_failed', detail: String(e).slice(0, 200), fallback: true }, 502);
  }
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
      'Access-Control-Allow-Origin': '*'
    }
  });
}
