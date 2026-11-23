import datetime
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DOCS_DIR = ROOT / "docs"
POSTS_DIR = DOCS_DIR / "posts"
CONFIG_FILE = ROOT / "config.json"
TOPICS_FILE = ROOT / "topics.json"
PUBLISHED_FILE = ROOT / "published_topics.json"

DEFAULT_CONFIG = {
    "site_title": "SmartPick Daily",
    "site_tagline": "Practical, honest guides on everyday tech, workspace gear, and smart essentials.",
    "site_url": "https://Aadeshmasih0-glitch.github.io/smartpick-daily",
    "author_name": "Editorial Team",
    "amazon_domain": "amazon.in",
    "default_amazon_tag": "Adesh00308-21",
    "adsense_client_id": "",
    "groq_model": "llama-3.3-70b-versatile"
}

DEFAULT_TOPICS = [
    {"topic": "Best Budget Ergonomic Desk Accessories Under ₹2,000 for Long Work Hours", "category": "Workspace Gear"},
    {"topic": "How to Choose a Durable Laptop Stand for Better Posture at Home", "category": "Workspace Gear"},
    {"topic": "Essential Two-Wheeler Maintenance Kit Every Daily Commuter Should Keep", "category": "Bike & Commute"},
    {"topic": "Best Anti-Theft and Waterproof Laptop Backpacks for Daily Office Travel", "category": "Bike & Commute"},
    {"topic": "Top 5 Compact Power Banks for Travel and Emergency Backup in India", "category": "Everyday Tech"},
    {"topic": "How to Organize Desk Cables Cleanly on a Tight Budget", "category": "Workspace Gear"},
    {"topic": "Best Budget Mechanical Keyboards for Coding and Daily Typing", "category": "Everyday Tech"},
    {"topic": "Essential Helmet Care and Riding Gloves Guide for City Riders", "category": "Bike & Commute"},
    {"topic": "Smart LED Desk Lamps That Reduce Eye Strain During Night Study", "category": "Workspace Gear"},
    {"topic": "Best Portable SSDs and Pen Drives for Safe File Backups", "category": "Everyday Tech"},
    {"topic": "How to Pick a Reliable Surge Protector for Home Computers and Routers", "category": "Everyday Tech"},
    {"topic": "Must-Have Compact Tool Kit for Home and Basic Vehicle Repairs", "category": "Smart Essentials"},
    {"topic": "Best Wireless Mice for Comfort and Productivity Under ₹1,500", "category": "Workspace Gear"},
    {"topic": "Rainy Season Riding Gear: Waterproof Covers and Phone Mounts Guide", "category": "Bike & Commute"},
    {"topic": "How to Improve Wi-Fi Coverage in a Multi-Room Home Without Expensive Routers", "category": "Everyday Tech"},
    {"topic": "Best Insulated Water Bottles and Lunch Boxes for Office Commuters", "category": "Smart Essentials"},
    {"topic": "Simple Digital Minimalism Habits to Save 1 Hour Every Day", "category": "Productivity"},
    {"topic": "Best Noise-Isolating Earphones for Focus in Noisy Environments", "category": "Everyday Tech"},
    {"topic": "How to Maintain Your Laptop Battery Health for 4+ Years", "category": "Everyday Tech"},
    {"topic": "Essential Travel Organizer Pouches for Chargers, Cables, and Adapters", "category": "Smart Essentials"},
    {"topic": "Best Budget Microphones for Clear Online Meetings and Voiceovers", "category": "Workspace Gear"},
    {"topic": "How to Set Up a Distraction-Free Study Corner in a Small Room", "category": "Productivity"},
    {"topic": "Top Tire Inflators and Puncture Repair Kits for Stress-Free Rides", "category": "Bike & Commute"},
    {"topic": "Best USB-C Hubs and Multiport Adapters for Modern Laptops", "category": "Everyday Tech"},
    {"topic": "How to Clean Electronics Safely: Screens, Keyboards, and Ports", "category": "Smart Essentials"},
    {"topic": "Best Affordable Chair Cushions and Lumbar Supports for Back Comfort", "category": "Workspace Gear"},
    {"topic": "Smart Plugs and Timers: Simple Ways to Automate Home Appliances Safely", "category": "Everyday Tech"},
    {"topic": "How to Build a Weekly Meal and Expense Tracker in 15 Minutes", "category": "Productivity"},
    {"topic": "Best Compact Tripod and Phone Mounts for Hands-Free Video Calls", "category": "Workspace Gear"},
    {"topic": "Essential First-Aid and Emergency Car/Bike Kit Checklist", "category": "Smart Essentials"}
]


def load_or_init_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(default, indent=2, ensure_ascii=False), encoding="utf-8")
    return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:70] or f"post-{int(datetime.datetime.utcnow().timestamp())}"


def clean_api_key(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", raw)


def call_ai(prompt: str, api_key: str, cfg: dict) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": cfg.get("groq_model", "llama-3.3-70b-versatile"),
        "messages": [
            {"role": "system", "content": "You are a helpful editorial writer. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Mozilla/5.0"
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Groq API Error {e.code}: {err_body}") from e


def replenish_topics(api_key: str, cfg: dict, existing_topics: list, published: list):
    used_titles = {t["topic"] for t in existing_topics} | {p["topic"] for p in published}
    prompt = f"""Generate 15 new evergreen, 100% safe, practical buying-guide or how-to article topics in everyday tech, workspace gear, bike/commute essentials, and productivity.
Avoid medical, legal, financial, or get-rich-quick claims.
Do NOT repeat any of these existing topics: {json.dumps(list(used_titles)[:30])}
Return ONLY a JSON object with a single key "topics" containing an array of objects with keys "topic" and "category"."""
    raw = call_ai(prompt, api_key, cfg)
    parsed = json.loads(raw)
    new_items = parsed.get("topics", []) if isinstance(parsed, dict) else parsed
    if isinstance(new_items, list):
        for item in new_items:
            if isinstance(item, dict) and "topic" in item and "category" in item:
                if item["topic"] not in used_titles:
                    existing_topics.append(item)
        save_json(TOPICS_FILE, existing_topics)


def generate_article_data(topic: str, category: str, api_key: str, cfg: dict) -> dict:
    prompt = f"""Write a helpful, honest, human-friendly evergreen guide on the topic: "{topic}" (Category: {category}).

Safety & Quality Rules:
- 100% original, practical, and easy to read.
- No medical, legal, or financial advice. No exaggerated or fake claims.
- Do NOT invent specific fake prices or fake user reviews. Give practical buying criteria and real-world pros/cons.
- Include 3 helpful product types/recommendations with clean Amazon search keywords.

Return ONLY valid JSON with this exact schema:
{{
  "title": "Clear, engaging article title",
  "meta_description": "140-155 character SEO summary",
  "reading_time": "5 min read",
  "intro": "2-3 sentence relatable introduction",
  "sections": [
    {{
      "heading": "Section heading",
      "body": "2-3 clear paragraphs (use \\n\\n between paragraphs)",
      "bullets": ["Practical point 1", "Practical point 2", "Practical point 3"]
    }}
  ],
  "recommendations": [
    {{
      "name": "Product Type Name",
      "best_for": "Who this is best for",
      "why_it_works": "1-2 sentences on what to look for",
      "search_keyword": "clean amazon search keyword"
    }}
  ],
  "faqs": [
    {{
      "question": "Common buyer question",
      "answer": "Clear, honest answer"
    }}
  ]
}}"""
    raw = call_ai(prompt, api_key, cfg)
    return json.loads(raw)


def build_amazon_link(keyword: str, domain: str, tag: str) -> str:
    q = urllib.parse.quote_plus(keyword.strip())
    if tag:
        return f"https://www.{domain}/s?k={q}&tag={urllib.parse.quote_plus(tag)}"
    return f"https://www.{domain}/s?k={q}"


def adsense_snippet(client_id: str) -> str:
    if not client_id:
        return ""
    safe_id = html.escape(client_id)
    return f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={safe_id}" crossorigin="anonymous"></script>'


COMMON_CSS = """
:root { --bg: #f8fafc; --surface: #ffffff; --text: #0f172a; --muted: #475569; --accent: #0f766e; --accent-light: #f0fdfa; --border: #e2e8f0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; }
header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 1.25rem 1.5rem; }
.nav-inner { max-width: 860px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
.brand { font-size: 1.25rem; font-weight: 700; color: var(--text); text-decoration: none; }
.brand span { color: var(--accent); }
.container { max-width: 860px; margin: 2rem auto; padding: 0 1.25rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.25rem; }
.badge { display: inline-block; font-size: 0.78rem; font-weight: 600; color: var(--accent); background: var(--accent-light); padding: 0.2rem 0.65rem; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.03em; }
.meta { color: var(--muted); font-size: 0.9rem; margin: 0.5rem 0 1rem; }
.disclosure { background: #fffbeb; border: 1px solid #fde68a; color: #78350f; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.85rem; margin-bottom: 1.5rem; }
.rec-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
.rec-card { border: 1px solid var(--border); border-radius: 10px; padding: 1.15rem; background: var(--bg); display: flex; flex-direction: column; justify-content: space-between; }
.btn { display: inline-block; margin-top: 0.85rem; background: var(--accent); color: #ffffff; text-decoration: none; padding: 0.55rem 1rem; border-radius: 8px; font-weight: 600; font-size: 0.9rem; text-align: center; }
.btn:hover { opacity: 0.92; }
h1 { font-size: 1.9rem; line-height: 1.25; margin: 0.5rem 0; }
h2 { font-size: 1.35rem; margin-top: 1.75rem; }
footer { text-align: center; color: var(--muted); font-size: 0.85rem; padding: 2rem 1rem; border-top: 1px solid var(--border); margin-top: 3rem; }
a { color: var(--accent); }
"""


def render_post_html(article: dict, category: str, date_str: str, cfg: dict, tag: str) -> str:
    title = html.escape(article["title"])
    desc = html.escape(article.get("meta_description", ""))
    read_time = html.escape(article.get("reading_time", "5 min read"))
    intro = html.escape(article.get("intro", ""))
    site_title = html.escape(cfg["site_title"])

    sections_html = []
    for sec in article.get("sections", []):
        h = html.escape(sec.get("heading", ""))
        paras = "".join(f"<p>{html.escape(p.strip())}</p>" for p in sec.get("body", "").split("\n\n") if p.strip())
        bullets = sec.get("bullets", [])
        bullets_html = f"<ul>{''.join(f'<li>{html.escape(b)}</li>' for b in bullets)}</ul>" if bullets else ""
        sections_html.append(f"<section><h2>{h}</h2>{paras}{bullets_html}</section>")

    recs_html = []
    for rec in article.get("recommendations", []):
        r_name = html.escape(rec.get("name", ""))
        r_best = html.escape(rec.get("best_for", ""))
        r_why = html.escape(rec.get("why_it_works", ""))
        link = html.escape(build_amazon_link(rec.get("search_keyword", r_name), cfg["amazon_domain"], tag))
        recs_html.append(f"""
        <div class="rec-card">
          <div><span class="badge">{r_best}</span><h3 style="margin:0.5rem 0 0.35rem;">{r_name}</h3><p style="font-size:0.92rem; color:var(--muted); margin:0;">{r_why}</p></div>
          <a class="btn" href="{link}" target="_blank" rel="nofollow sponsored noopener">Check Options on Amazon &rarr;</a>
        </div>""")

    faqs_html = [f"<div style='margin-bottom:1rem;'><strong>{html.escape(f.get('question',''))}</strong><p style='margin:0.25rem 0;'>{html.escape(f.get('answer',''))}</p></div>" for f in article.get("faqs", [])]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | {site_title}</title><meta name="description" content="{desc}">
  {adsense_snippet(cfg.get("adsense_client_id", ""))}<style>{COMMON_CSS}</style>
</head>
<body>
  <header><div class="nav-inner"><a class="brand" href="../index.html">{site_title}<span>.</span></a><a href="../index.html" style="text-decoration:none; font-weight:500;">All Guides</a></div></header>
  <main class="container">
    <article class="card">
      <span class="badge">{html.escape(category)}</span><h1>{title}</h1>
      <div class="meta">Published {html.escape(date_str)} &bull; {read_time}</div>
      <div class="disclosure"><strong>Transparency Note:</strong> As an Amazon Associate, we earn from qualifying purchases at no extra cost to you.</div>
      <p style="font-size:1.08rem;">{intro}</p>{''.join(sections_html)}
      <h2>Top Practical Picks to Consider</h2><div class="rec-grid">{''.join(recs_html)}</div>
      <h2>Frequently Asked Questions</h2>{''.join(faqs_html)}
    </article>
  </main>
  <footer>&copy; {datetime.datetime.utcnow().year} {site_title}. Built for practical, evergreen everyday decisions.</footer>
</body>
</html>"""


def rebuild_index_and_feeds(published: list, cfg: dict):
    site_title = html.escape(cfg["site_title"])
    tagline = html.escape(cfg["site_tagline"])
    site_url = cfg["site_url"].rstrip("/")

    cards_html = []
    for item in reversed(published):
        t, d, c, dt, slug = html.escape(item["title"]), html.escape(item["meta_description"]), html.escape(item["category"]), html.escape(item["date"]), html.escape(item["slug"])
        cards_html.append(f"""
        <article class="card">
          <span class="badge">{c}</span>
          <h2 style="margin:0.5rem 0 0.25rem;"><a href="posts/{slug}.html" style="text-decoration:none; color:var(--text);">{t}</a></h2>
          <div class="meta">{dt}</div>
          <p style="margin:0 0 0.75rem; color:var(--muted);">{d}</p>
          <a href="posts/{slug}.html" style="font-weight:600; text-decoration:none;">Read Guide &rarr;</a>
        </article>""")
    if not cards_html:
        cards_html.append('<div class="card"><p>First evergreen guide publishing shortly...</p></div>')

    (DOCS_DIR / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{site_title} — Practical Everyday Guides</title><meta name="description" content="{tagline}">
  {adsense_snippet(cfg.get("adsense_client_id", ""))}<style>{COMMON_CSS}</style>
</head>
<body>
  <header><div class="nav-inner"><a class="brand" href="index.html">{site_title}<span>.</span></a><a href="rss.xml" style="text-decoration:none; font-size:0.9rem;">RSS Feed</a></div></header>
  <main class="container">
    <div class="card" style="background:var(--accent-light); border-color:#99f6e4;"><h1 style="margin-top:0;">{site_title}</h1><p style="margin-bottom:0; color:var(--muted);">{tagline}</p></div>
    {''.join(cards_html)}
  </main>
  <footer>&copy; {datetime.datetime.utcnow().year} {site_title} &bull; <a href="sitemap.xml">Sitemap</a></footer>
</body>
</html>""", encoding="utf-8")

    urls = [f"  <url><loc>{site_url}/index.html</loc></url>"] + [f"  <url><loc>{site_url}/posts/{i['slug']}.html</loc><lastmod>{i['date']}</lastmod></url>" for i in published]
    (DOCS_DIR / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>", encoding="utf-8")

    rss_items = [f"  <item><title>{html.escape(i['title'])}</title><link>{site_url}/posts/{i['slug']}.html</link><description>{html.escape(i['meta_description'])}</description></item>" for i in reversed(published[-20:])]
    (DOCS_DIR / "rss.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{site_title}</title><link>{site_url}</link><description>{tagline}</description>\n' + "\n".join(rss_items) + "\n</channel></rss>", encoding="utf-8")


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    cfg = load_or_init_json(CONFIG_FILE, DEFAULT_CONFIG)
    topics = load_or_init_json(TOPICS_FILE, DEFAULT_TOPICS)
    published = load_or_init_json(PUBLISHED_FILE, [])

    api_key = clean_api_key(os.environ.get("GEMINI_API_KEY", ""))
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY environment variable.")
    tag = os.environ.get("AMAZON_TAG", "").strip() or cfg.get("default_amazon_tag", "")

    published_topics = {p["topic"] for p in published}
    pending = [t for t in topics if t["topic"] not in published_topics]
    if len(pending) < 2:
        replenish_topics(api_key, cfg, topics, published)
        topics = load_or_init_json(TOPICS_FILE, DEFAULT_TOPICS)
        pending = [t for t in topics if t["topic"] not in published_topics]
    if not pending:
        return

    chosen = pending[0]
    article = generate_article_data(chosen["topic"], chosen["category"], api_key, cfg)
    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    slug = slugify(article["title"])

    (POSTS_DIR / f"{slug}.html").write_text(render_post_html(article, chosen["category"], date_str, cfg, tag), encoding="utf-8")
    published.append({
        "topic": chosen["topic"],
        "title": article["title"],
        "meta_description": article.get("meta_description", ""),
        "category": chosen["category"],
        "date": date_str,
        "slug": slug,
    })
    save_json(PUBLISHED_FILE, published)
    rebuild_index_and_feeds(published, cfg)
    print(f"Published: {article['title']} -> docs/posts/{slug}.html")


if __name__ == "__main__":
    main()
