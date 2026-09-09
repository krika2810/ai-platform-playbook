#!/usr/bin/env python3
"""Build index.html from data/reels.json + data/content/<id>.json authored entries."""
import json, html, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
reels = json.load(open(f'{ROOT}/data/reels.json'))
content = {}
cdir = f'{ROOT}/data/content'
for f in os.listdir(cdir):
    if f.endswith('.json'):
        d = json.load(open(f'{cdir}/{f}'))
        content[d['id']] = d

GLOSSARY = json.load(open(f'{ROOT}/data/glossary.json'))

def esc(s): return html.escape(s or '', quote=False)

TIP_RE = {}
def tipify(text):
    """Wrap first occurrences of glossary terms in tooltip spans."""
    if not text: return ''
    out = esc(text)
    # longest-first so multiword terms win
    for term in sorted(GLOSSARY, key=len, reverse=True):
        pat = re.compile(r'(?<![\w>])(' + re.escape(esc(term)) + r')(?![\w<])', re.I)
        def rep(m):
            t = m.group(1)
            key = term.lower()
            if TIP_RE.get(key, 0) >= 1: return t  # one tooltip per term per page section
            TIP_RE[key] = TIP_RE.get(key, 0) + 1
            return f'<span class="tip" tabindex="0">{t}<span class="tip-bubble" role="tooltip">{esc(GLOSSARY[term])}</span></span>'
        out = pat.sub(rep, out, count=1)
    return out

def fresh_tips():
    TIP_RE.clear()

ERAS = [
    ("era-rest", "The Rest - Foundations, Early Explainers, Career & Concepts", "Dec 2022 - Jul 2026",
     "Everything outside the two seasons: cloud architecture fundamentals, the first AI explainers, architect skills and governance, career strategy and interview craft, plus one-off concepts and announcements - all in the order he posted them."),
    ("era-season1", "Season 1 - AI Solution Architect Transformation", "Jul 31 - Aug 22, 2026",
     "His first structured series: ten episodes that walk a classic solution architect into AI infrastructure - certifications, GPU infrastructure, inference gateways, scaling, private hosting, edge, caching, and DR."),
    ("era-season2", "Season 2 - AI Platform Solution Architect Transformation", "Aug 25 - Sep 8, 2026",
     "The current series: eight episodes on building the shared enterprise AI platform - MCP hub, multi-tenancy, prompt registry, agent SDK, RAG-as-a-service, evaluation, and the unified tool catalog."),
]

def era_for(date):
    if date < '20260731': return 0
    if date < '20260825': return 1
    return 2

def fmt_date(d):
    from datetime import datetime
    return datetime.strptime(d, '%Y%m%d').strftime('%b %-d, %Y')

parts = []
total = len(reels)
done = sum(1 for r in reels if r['id'] in content)

# group reels by era, preserving chronological order
by_era = {}
for r in reels:
    by_era.setdefault(era_for(r['date']), []).append(r)

nav = ''.join(f'<a href="#{e[0]}">{esc(e[1])}</a>' for e in ERAS if e[0].split("-",1)[1] and by_era.get(ERAS.index(e)) is not None)

hero_stats = f'{total} reels &middot; {sum(len(v) for k,v in by_era.items())} explained &middot; {fmt_date(reels[0]["date"])} &rarr; {fmt_date(reels[-1]["date"])}'

toc_items = []
for ei,(eid, ename, edates, eintro) in enumerate(ERAS):
    n = len(by_era.get(ei, []))
    if not n: continue
    toc_items.append(f'''<a class="toc-card" href="#{eid}">
      <div class="toc-name">{esc(ename)}</div>
      <div class="toc-meta">{esc(edates)} &middot; {n} reels</div>
    </a>''')
toc = f'''<nav class="toc" aria-label="Table of contents">
  <div class="wrap">
    <div class="toc-label">Jump to a section</div>
    <div class="toc-grid">{"".join(toc_items)}
    <a class="toc-card" href="#glossary">
      <div class="toc-name">Glossary</div>
      <div class="toc-meta">every hard term, one line each</div>
    </a></div>
  </div>
</nav>'''

for ei,(eid, ename, edates, eintro) in enumerate(ERAS):
    era_reels = by_era.get(ei, [])
    if not era_reels: continue
    parts.append(f'''<section class="era" id="{eid}">
  <div class="wrap">
    <div class="era-head">
      <div class="era-dates">{esc(edates)}</div>
      <h2>{esc(ename)}</h2>
      <p>{esc(eintro)}</p>
      <div class="era-count">{len(era_reels)} reels</div>
    </div>
  </div>''')
    for r in era_reels:
        c = content.get(r['id'], {})
        fresh_tips()
        title = esc(c.get('title') or (r['caption'][:80] if r['caption'] else 'Untitled reel'))
        oneliner = tipify(c.get('oneliner',''))
        says = tipify(c.get('says',''))
        explained = ''.join(f'<p>{tipify(p)}</p>' for p in c.get('explained',[]))
        takeaway = tipify(c.get('takeaway',''))
        badges = ''.join(f'<span class="badge">{esc(b)}</span>' for b in c.get('badges',[]))
        dup = '<span class="badge dup">duplicate post</span>' if c.get('duplicate') else ''
        embed_url = f"https://www.instagram.com/reel/{r['id']}/embed"
        parts.append(f'''  <article class="reel" id="reel-{r['n']}" data-date="{r['date']}">
    <div class="wrap reel-grid">
      <aside class="rail">
        <div class="num">{r['n']}<span class="of">/{total}</span></div>
        <div class="date">{fmt_date(r['date'])}</div>
      </aside>
      <div class="body">
        <div class="badges">{badges}{dup}</div>
        <h3>{title}</h3>
        <div class="oneliner"><span class="ol-label">In one line</span>{oneliner}</div>
        <div class="says"><span class="sec-label">What he says</span><p>{says}</p></div>
        <div class="explained"><span class="sec-label">The idea, explained</span>{explained}</div>
        <div class="takeaway"><span class="tk-label">Why it matters</span>{takeaway}</div>
        <div class="reel-embed" data-embed="{embed_url}"><span class="embed-note">Instagram reel - video loads as you scroll to it</span></div>
        <a class="watch" href="{r['url']}" target="_blank" rel="noopener">Watch on Instagram &nearr;</a>
      </div>
    </div>
  </article>''')
    parts.append('</section>')

gloss_items = ''.join(f'<div class="g-item"><dt>{esc(t)}</dt><dd>{esc(d)}</dd></div>' for t,d in sorted(GLOSSARY.items(), key=lambda x:x[0].lower()))

CSS = open(f'{ROOT}/style.css').read()

html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The AI Architect Reel Companion - all {total} reels of @architect_it_cloud, explained</title>
<meta name="description" content="Every reel Govindh Varadharajan (@architect_it_cloud) has posted, in order, each one explained in plain English - from the first cloud fundamentals reel to Season 2 of the AI Platform Solution Architect series.">
<style>
{CSS}
</style>
</head>
<body>
<header class="top">
  <div class="wrap bar">
    <div class="brand">The <span>Reel Companion</span></div>
    <nav>{nav}<a href="#glossary">Glossary</a></nav>
  </div>
</header>

<section class="hero">
  <div class="wrap">
    <div class="kicker">@architect_it_cloud &middot; Govindh Varadharajan &middot; AI Architect &middot; 2&times; LinkedIn Top Voice</div>
    <h1>Every reel he has posted.<br>Explained in plain English.</h1>
    <div class="bigcount"><span class="n">{total}</span><span class="l">reels, from the first to the latest, in the order he posted them</span></div>
    <div class="sort-toggle" role="group" aria-label="Sort reels by posted date">
      <span class="sort-label">Order</span>
      <div class="seg">
        <button type="button" data-sort="asc" aria-pressed="true">Oldest first</button>
        <button type="button" data-sort="desc" aria-pressed="false">Newest first</button>
      </div>
    </div>
    <p class="sub">Read it like a book. Each reel gets its core message in one highlighted line, a summary of what he actually says, a full plain-English explanation, and the reason it matters - with hover tooltips on every hard term and a link to the original reel.</p>
    <div class="hero-stats">{hero_stats}</div>
  </div>
</section>

{toc}\n{''.join(parts)}

<section class="glossary" id="glossary">
  <div class="wrap">
    <h2>Glossary - every hard term, one line each</h2>
    <dl class="g-grid">{gloss_items}</dl>
  </div>
</section>

<footer>
  <div class="wrap">
    <p>Built from the public reels of <a href="https://www.instagram.com/architect_it_cloud/" target="_blank" rel="noopener">@architect_it_cloud</a> - {total} reels transcribed and explained, {fmt_date(reels[0]['date'])} to {fmt_date(reels[-1]['date'])}. Not affiliated; a learning companion for his content.</p>
  </div>
</footer>
<script>
// mobile tap-to-toggle tooltips
document.addEventListener('click', e => {{
  const t = e.target.closest('.tip');
  document.querySelectorAll('.tip.open').forEach(x => {{ if (x !== t) x.classList.remove('open'); }});
  if (t) t.classList.toggle('open');
}});

// sort toggle: oldest-first (default) or newest-first, by posted date
const sortBtns = [...document.querySelectorAll('[data-sort]')];
function applySort(dir) {{
  const eras = [...document.querySelectorAll('.era')];
  eras.forEach(s => {{
    [...s.querySelectorAll('.reel')]
      .sort((a, b) => dir === 'asc' ? a.dataset.date.localeCompare(b.dataset.date) : b.dataset.date.localeCompare(a.dataset.date))
      .forEach(a => s.appendChild(a));
  }});
  const eraKey = s => Math.min(...[...s.querySelectorAll('.reel')].map(r => +r.dataset.date));
  const glossary = document.getElementById('glossary');
  eras.sort((a, b) => dir === 'asc' ? eraKey(a) - eraKey(b) : eraKey(b) - eraKey(a))
      .forEach(s => document.body.insertBefore(s, glossary));
  sortBtns.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.sort === dir)));
  document.querySelectorAll('.tip.open').forEach(x => x.classList.remove('open'));
}}
sortBtns.forEach(b => b.addEventListener('click', () => applySort(b.dataset.sort)));

// lazy Instagram embeds: swap in the official iframe only when the card nears the viewport
const embedIO = new IntersectionObserver(entries => {{
  entries.forEach(en => {{
    if (!en.isIntersecting) return;
    const slot = en.target;
    embedIO.unobserve(slot);
    const f = document.createElement('iframe');
    f.src = slot.dataset.embed;
    f.loading = 'lazy';
    f.setAttribute('allowfullscreen', '');
    f.setAttribute('allow', 'encrypted-media; clipboard-write');
    f.title = 'Instagram reel embed';
    slot.textContent = '';
    slot.appendChild(f);
  }});
}}, {{ rootMargin: '900px 0px' }});
document.querySelectorAll('.reel-embed[data-embed]').forEach(s => embedIO.observe(s));
</script>
</body>
</html>'''

open(f'{ROOT}/index.html','w').write(html_doc)
print(f'built: {total} reels, {done} with authored content, {len(html_doc)} bytes')
