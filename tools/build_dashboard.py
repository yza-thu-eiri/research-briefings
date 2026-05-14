import datetime as dt
import html
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIEFINGS = ROOT / "briefings"


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def first_match(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.I | re.S)
    return strip_tags(match.group(1)) if match else default


def section_html(text: str, title: str) -> str:
    pattern = rf"<h2>\s*{re.escape(title)}\s*</h2>(.*?)(?=<h2>|</main>)"
    match = re.search(pattern, text, flags=re.I | re.S)
    return match.group(1) if match else ""


def extract_papers(slug: str, text: str) -> list[dict]:
    papers: list[dict] = []
    seen: set[str] = set()

    read_now = section_html(text, "Read Now")
    for idx, match in enumerate(
        re.finditer(r"<h3>\s*(?:\d+\.\s*)?<a\s+href=\"([^\"]+)\">(.*?)</a>\s*</h3>", read_now, flags=re.I | re.S),
        start=1,
    ):
        url, title = match.groups()
        title = strip_tags(title)
        key = f"{slug}:read:{idx}:{url}"
        seen.add(url)
        papers.append({"id": key, "title": title, "url": html.unescape(url), "section": "Read Now", "priority": idx})

    watchlist = section_html(text, "Watchlist")
    for idx, match in enumerate(
        re.finditer(r"<li>\s*<a\s+href=\"([^\"]+)\">(.*?)</a>", watchlist, flags=re.I | re.S),
        start=1,
    ):
        url, title = match.groups()
        if url in seen:
            continue
        title = strip_tags(title)
        key = f"{slug}:watch:{idx}:{url}"
        papers.append({"id": key, "title": title, "url": html.unescape(url), "section": "Watchlist", "priority": idx})

    if not papers:
        for idx, match in enumerate(
            re.finditer(r"<a\s+href=\"([^\"]*(?:arxiv\.org|microsoft\.com|aclanthology\.org)[^\"]*)\">(.*?)</a>", text, flags=re.I | re.S),
            start=1,
        ):
            url, title = match.groups()
            if url in seen:
                continue
            seen.add(url)
            papers.append(
                {
                    "id": f"{slug}:link:{idx}:{url}",
                    "title": strip_tags(title),
                    "url": html.unescape(url),
                    "section": "Papers",
                    "priority": idx,
                }
            )

    return papers


def infer_date(slug: str) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", slug)
    return match.group(1) if match else ""


def infer_topic(title: str, slug: str) -> str:
    if "：" in title:
        return title.split("：", 1)[1].strip()
    parts = slug.split("-")
    if len(parts) > 3:
        return " / ".join(parts[3:-4] or parts[3:])
    return title


def load_briefings() -> list[dict]:
    result: list[dict] = []
    for page in sorted(BRIEFINGS.glob("*/index.html"), reverse=True):
        slug = page.parent.name
        text = page.read_text(encoding="utf-8")
        title = first_match(r"<h1[^>]*>(.*?)</h1>", text, slug)
        result.append(
            {
                "slug": slug,
                "date": infer_date(slug),
                "title": title,
                "topic": infer_topic(title, slug),
                "url": f"briefings/{slug}/",
                "papers": extract_papers(slug, text),
            }
        )
    return result


def build_html(data: list[dict]) -> str:
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = json.dumps(data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Research Briefings</title>
<style>
:root {{
  color-scheme: light;
  --paper: #f7f2e8;
  --ink: #1d241f;
  --muted: #667069;
  --line: #d5c8b4;
  --surface: #fffdf8;
  --accent: #006c67;
  --accent-2: #a4491d;
  --ok: #137a4f;
  --no: #9b3324;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background:
    linear-gradient(90deg, rgba(29,36,31,.055) 1px, transparent 1px) 0 0 / 28px 28px,
    linear-gradient(180deg, #efe6d8 0%, var(--paper) 320px, #fbfaf6 100%);
  color: var(--ink);
  font-family: Georgia, "Times New Roman", "Microsoft YaHei", "PingFang SC", serif;
}}
button, input {{ font: inherit; }}
a {{ color: inherit; }}
.shell {{ max-width: 1180px; margin: 0 auto; padding: 34px 20px 56px; }}
.masthead {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 22px;
  align-items: end;
  border-bottom: 2px solid var(--ink);
  padding-bottom: 22px;
}}
h1 {{ margin: 0; font-size: clamp(34px, 7vw, 82px); line-height: .92; letter-spacing: 0; }}
.meta {{ color: var(--muted); font-size: 14px; text-align: right; line-height: 1.7; }}
.toolbar {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin: 22px 0;
}}
.search {{
  min-width: min(100%, 310px);
  flex: 1;
  border: 1px solid var(--line);
  background: var(--surface);
  padding: 11px 13px;
  border-radius: 6px;
  color: var(--ink);
}}
.seg {{ display: inline-flex; border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: var(--surface); }}
.seg button {{ border: 0; background: transparent; padding: 10px 13px; cursor: pointer; color: var(--muted); }}
.seg button.active {{ background: var(--ink); color: #fffdf8; }}
.layout {{ display: grid; grid-template-columns: 380px minmax(0, 1fr); gap: 20px; align-items: start; }}
.list {{ display: grid; gap: 12px; }}
.briefing-card {{
  width: 100%;
  text-align: left;
  border: 1px solid var(--line);
  background: rgba(255,253,248,.88);
  border-radius: 7px;
  padding: 14px;
  cursor: pointer;
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}}
.briefing-card:hover, .briefing-card.active {{
  transform: translateY(-1px);
  border-color: var(--ink);
  box-shadow: 0 12px 30px rgba(42, 34, 22, .10);
}}
.card-top {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }}
.date {{ font-variant-numeric: tabular-nums; color: var(--accent-2); font-weight: 700; }}
.status {{ color: var(--muted); font-size: 13px; white-space: nowrap; }}
.topic {{ margin: 7px 0 11px; font-size: 18px; line-height: 1.25; font-weight: 700; }}
.bar {{ height: 8px; border: 1px solid var(--line); border-radius: 99px; overflow: hidden; background: #eee4d4; }}
.bar span {{ display: block; height: 100%; width: 0; background: var(--ok); }}
.detail {{
  min-height: 520px;
  border: 1px solid var(--line);
  background: rgba(255,253,248,.94);
  border-radius: 7px;
  padding: 22px;
  position: sticky;
  top: 18px;
}}
.detail-head {{ display: flex; justify-content: space-between; gap: 18px; align-items: start; border-bottom: 1px solid var(--line); padding-bottom: 16px; }}
.detail h2 {{ margin: 0 0 8px; font-size: clamp(25px, 4vw, 44px); line-height: 1; letter-spacing: 0; }}
.open-original {{ display: inline-flex; align-items: center; border: 1px solid var(--ink); border-radius: 6px; padding: 9px 12px; text-decoration: none; white-space: nowrap; }}
.summary {{ display: flex; gap: 10px; flex-wrap: wrap; color: var(--muted); font-size: 14px; }}
.pill {{ border: 1px solid var(--line); border-radius: 99px; padding: 5px 9px; background: #f7efe2; }}
.paper-list {{ list-style: none; padding: 0; margin: 18px 0 0; display: grid; gap: 10px; }}
.paper {{
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  border: 1px solid var(--line);
  border-radius: 7px;
  padding: 12px;
  background: #fffaf1;
}}
.paper input {{ width: 22px; height: 22px; accent-color: var(--ok); margin-top: 2px; }}
.paper-title {{ font-size: 16px; font-weight: 700; line-height: 1.32; text-decoration: none; }}
.paper-title:hover {{ color: var(--accent); text-decoration: underline; }}
.paper-section {{ font-size: 12px; color: var(--muted); margin-top: 5px; }}
.mark {{ font-size: 22px; line-height: 1; color: var(--no); }}
.paper.done .mark {{ color: var(--ok); }}
.empty {{ color: var(--muted); padding: 36px 0; }}
@media (max-width: 860px) {{
  .masthead, .layout {{ grid-template-columns: 1fr; }}
  .meta {{ text-align: left; }}
  .detail {{ position: static; }}
}}
</style>
</head>
<body>
<main class="shell">
  <header class="masthead">
    <div>
      <h1>Research<br>Briefings</h1>
    </div>
    <div class="meta">
      <div>论文阅读看板</div>
      <div>Generated {generated}</div>
      <div id="globalStats"></div>
    </div>
  </header>
  <section class="toolbar" aria-label="filters">
    <input id="search" class="search" placeholder="搜索日期、主题或论文标题">
    <div class="seg" role="group" aria-label="status filter">
      <button type="button" data-filter="all" class="active">全部</button>
      <button type="button" data-filter="open">未完成</button>
      <button type="button" data-filter="done">已完成</button>
    </div>
  </section>
  <section class="layout">
    <div id="briefingList" class="list"></div>
    <article id="detail" class="detail"></article>
  </section>
</main>
<script>
const BRIEFINGS = {payload};
const storageKey = id => `researchBriefings.paper.${{id}}`;
let selected = location.hash ? decodeURIComponent(location.hash.slice(1)) : (BRIEFINGS[0] && BRIEFINGS[0].slug);
let filter = 'all';

function isDone(paper) {{ return localStorage.getItem(storageKey(paper.id)) === '1'; }}
function setDone(paper, value) {{
  if (value) localStorage.setItem(storageKey(paper.id), '1');
  else localStorage.removeItem(storageKey(paper.id));
}}
function progress(briefing) {{
  const total = briefing.papers.length;
  const done = briefing.papers.filter(isDone).length;
  return {{ total, done, open: total - done, pct: total ? Math.round(done / total * 100) : 0 }};
}}
function globalProgress() {{
  const papers = BRIEFINGS.flatMap(b => b.papers);
  const done = papers.filter(isDone).length;
  document.getElementById('globalStats').textContent = `${{done}} / ${{papers.length}} papers read`;
}}
function renderList() {{
  const q = document.getElementById('search').value.trim().toLowerCase();
  const list = document.getElementById('briefingList');
  list.innerHTML = '';
  BRIEFINGS
    .filter(b => {{
      const p = progress(b);
      if (filter === 'open' && p.open === 0) return false;
      if (filter === 'done' && (p.total === 0 || p.open > 0)) return false;
      const hay = [b.date, b.topic, b.title, ...b.papers.map(paper => paper.title)].join(' ').toLowerCase();
      return !q || hay.includes(q);
    }})
    .forEach(b => {{
      const p = progress(b);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'briefing-card' + (b.slug === selected ? ' active' : '');
      btn.innerHTML = `
        <div class="card-top"><span class="date">${{b.date || 'undated'}}</span><span class="status">${{p.done}}✓ / ${{p.open}}×</span></div>
        <div class="topic">${{b.topic}}</div>
        <div class="bar" aria-label="${{p.pct}} percent read"><span style="width:${{p.pct}}%"></span></div>
      `;
      btn.addEventListener('click', () => {{
        selected = b.slug;
        history.replaceState(null, '', '#' + encodeURIComponent(b.slug));
        render();
      }});
      list.appendChild(btn);
    }});
}}
function renderDetail() {{
  const detail = document.getElementById('detail');
  const b = BRIEFINGS.find(item => item.slug === selected) || BRIEFINGS[0];
  if (!b) {{
    detail.innerHTML = '<p class="empty">No briefings found.</p>';
    return;
  }}
  selected = b.slug;
  const p = progress(b);
  detail.innerHTML = `
    <div class="detail-head">
      <div>
        <h2>${{b.topic}}</h2>
        <div class="summary">
          <span class="pill">${{b.date}}</span>
          <span class="pill">${{p.done}} read</span>
          <span class="pill">${{p.open}} unread</span>
          <span class="pill">${{p.pct}}%</span>
        </div>
      </div>
      <a class="open-original" href="${{b.url}}">打开原文</a>
    </div>
    ${{b.papers.length ? '<ul class="paper-list"></ul>' : '<p class="empty">这个 briefing 没有抽取到论文链接。</p>'}}
  `;
  const ul = detail.querySelector('.paper-list');
  if (!ul) return;
  b.papers.forEach(paper => {{
    const li = document.createElement('li');
    li.className = 'paper' + (isDone(paper) ? ' done' : '');
    li.innerHTML = `
      <input type="checkbox" ${{isDone(paper) ? 'checked' : ''}} aria-label="mark as read">
      <div>
        <a class="paper-title" href="${{paper.url}}" target="_blank" rel="noopener">${{paper.title}}</a>
        <div class="paper-section">${{paper.section}}</div>
      </div>
      <div class="mark">${{isDone(paper) ? '✓' : '×'}}</div>
    `;
    li.querySelector('input').addEventListener('change', event => {{
      setDone(paper, event.target.checked);
      render();
    }});
    ul.appendChild(li);
  }});
}}
function render() {{
  globalProgress();
  renderList();
  renderDetail();
}}
document.getElementById('search').addEventListener('input', renderList);
document.querySelectorAll('.seg button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    filter = btn.dataset.filter;
    document.querySelectorAll('.seg button').forEach(b => b.classList.toggle('active', b === btn));
    renderList();
  }});
}});
render();
</script>
</body>
</html>
"""


def main() -> None:
    data = load_briefings()
    (ROOT / "index.html").write_text(build_html(data), encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote index.html with {len(data)} briefings and {sum(len(b['papers']) for b in data)} papers")


if __name__ == "__main__":
    main()
