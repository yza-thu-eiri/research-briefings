import argparse
import datetime as dt
import html
import json
import os
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIEFINGS = ROOT / "briefings"
COMMON_CHATGPT_PROJECT = "https://chatgpt.com/g/g-p-69f2d27eda0c8191ba40e9e8d36855ed-du-lun-wen/project"
DEFAULT_RESEARCH_WORKBENCH_STATE = pathlib.Path(
    r"E:\Git Repo\Research\.codex\reading_workbench\users\ziang\state\reading-state.json"
)
LEGACY_ONEDRIVE_STATE = pathlib.Path(r"C:\Users\ziang\OneDrive\ResearchReadingSync\state\reading-state.json")

CARD_TITLE_OVERRIDES = {
    "2026-05-14-Acceleration-Long-Context-network-first-briefing-zh": "KV cache enters learnable resource management",
    "2026-05-12-Agent-Deep-Research-Agents-network-first-briefing-zh": "Deep Research evaluation shifts toward process diagnosis",
    "2026-05-11-RAG-network-first-briefing-zh": "RAG shifts from more retrieval to better routing",
    "2026-05-09-Findings-Mechanistic-Interpretability-network-first-briefing-zh": "Interpretability evidence thresholds keep rising",
    "2026-05-06-Evaluation-Judge-Reliability-network-first-briefing-zh": "LLM Judge reliability enters protocol-sensitive territory",
    "2026-05-05-Agent-Deep-Research-Agents-network-first-briefing-zh": "Deep Research agents move from reports to process control",
    "2026-05-04-RAG-network-first-briefing-zh": "Adaptive routing becomes the new RAG mainline",
    "2026-05-02-Findings-Mechanistic-Interpretability-network-first-briefing-zh": "Mechanistic interpretability moves from explanation to verifiable intervention",
    "2026-04-30-Acceleration-Long-Context-network-first-briefing-zh": "Long-context bottlenecks concentrate around KV cache",
    "2026-04-29-Evaluation-Judge-Reliability-network-first-briefing-zh": "Judge evaluation must handle hallucinated citations and bias",
    "2026-04-28-Agent-Memory-State-network-first-briefing-zh": "Agent memory becomes the core long-running state",
}


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def first_match(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.I | re.S)
    return strip_tags(match.group(1)) if match else default


def infer_date(slug: str) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", slug)
    return match.group(1) if match else ""


def infer_topic(title: str, slug: str) -> str:
    for mark in ("：", ":"):
        if mark in title:
            return title.split(mark, 1)[1].strip()
    parts = slug.split("-")
    return " / ".join(parts[3:-4] or parts[3:]) if len(parts) > 3 else title


def shorten(value: str, limit: int) -> str:
    value = re.sub(r"[\[\]`*_#]", "", strip_tags(value))
    value = re.sub(r"\s+", " ", value).strip(" ，。；,;:")
    if len(value) <= limit:
        return value
    trimmed = value[:limit]
    split_at = max(trimmed.rfind(mark) for mark in ["，", "。", ",", ";", " "])
    if split_at > int(limit * 0.68):
        trimmed = trimmed[:split_at]
    return trimmed.rstrip(" ，。；,;:") + "..."


def section_html(text: str, title: str) -> str:
    pattern = rf"<h2[^>]*>\s*{re.escape(title)}\s*</h2>(.*?)(?=<h2|</main>)"
    match = re.search(pattern, text, flags=re.I | re.S)
    return match.group(1) if match else ""


def section_by_heading(text: str, headings: list[str]) -> str:
    for heading in headings:
        pattern = rf"<h2[^>]*>\s*{re.escape(heading)}\s*</h2>(.*?)(?=<h2|</main>)"
        match = re.search(pattern, text, flags=re.I | re.S)
        if match:
            return match.group(1)
        pattern = rf"<h2[^>]*>.*?{re.escape(heading)}.*?</h2>(.*?)(?=<h2|</main>)"
        match = re.search(pattern, text, flags=re.I | re.S)
        if match:
            return match.group(1)
    return ""


def extract_papers(slug: str, text: str) -> list[dict]:
    papers: list[dict] = []
    seen: set[str] = set()
    for section_name in ("Read Now", "Watchlist"):
        section = section_html(text, section_name)
        section_key = "read" if section_name == "Read Now" else "watch"
        for idx, match in enumerate(
            re.finditer(r"<a\s+href=\"([^\"]+)\">(.*?)</a>", section, flags=re.I | re.S),
            start=1,
        ):
            url, title = match.groups()
            url = html.unescape(url)
            if not re.search(r"arxiv\.org|microsoft\.com|aclanthology\.org|openreview\.net|github\.com|doi\.org", url, re.I):
                continue
            if url in seen:
                continue
            seen.add(url)
            papers.append(
                {
                    "id": f"{slug}:{section_key}:{idx}:{url}",
                    "title": strip_tags(title),
                    "url": url,
                    "section": section_name,
                    "priority": idx,
                }
            )
    return papers


def extract_core_points(text: str) -> list[str]:
    section = section_by_heading(text, ["需要知道", "Key Patterns", "What I Learned"])
    points = [shorten(match.group(1), 42) for match in re.finditer(r"<strong>(.*?)</strong>", section, flags=re.I | re.S)]
    points = [point for point in points if point and not point.lower().startswith("why now")]
    if len(points) >= 2:
        return points[:2]
    paragraphs = [shorten(match.group(1), 48) for match in re.finditer(r"<p[^>]*>(.*?)</p>", text, flags=re.I | re.S)]
    return [p for p in paragraphs if p][:2]


def short_paper_title(title: str) -> str:
    title = re.split(r":\s+", strip_tags(title), maxsplit=1)[0]
    title = re.sub(r"\b(A|An|The)\b\s+", "", title, flags=re.I)
    return shorten(title, 30)


def extract_kicker(text: str, topic: str, papers: list[dict]) -> str:
    points = extract_core_points(text)
    read_now = [paper for paper in papers if paper.get("section") == "Read Now"][:2]
    paper_names = " / ".join(short_paper_title(paper["title"]) for paper in read_now)
    pieces = []
    if points:
        pieces.append("；".join(points[:2]))
    if paper_names:
        pieces.append(f"重点看 {paper_names}")
    return shorten(f"{topic}：{'；'.join(pieces or [topic])}", 140)


def extract_card_title(slug: str, text: str, topic: str) -> str:
    if slug in CARD_TITLE_OVERRIDES:
        return CARD_TITLE_OVERRIDES[slug]
    points = extract_core_points(text)
    return shorten(points[0] if points else topic, 28)


def extract_frontier_observation(text: str) -> str:
    section = section_by_heading(text, ["前沿变化观察", "Key Patterns", "What I Learned"])
    points = [shorten(match.group(1), 48) for match in re.finditer(r"<strong>(.*?)</strong>", section, flags=re.I | re.S)]
    points = [point for point in points if point and not point.lower().startswith("why now")]
    if points:
        return "；".join(points[:3])
    paragraphs = [shorten(match.group(1), 64) for match in re.finditer(r"<p[^>]*>(.*?)</p>", section, flags=re.I | re.S)]
    return "；".join(paragraph for paragraph in paragraphs[:2] if paragraph)


def load_briefings() -> list[dict]:
    result: list[dict] = []
    for page in sorted(BRIEFINGS.glob("*/index.html"), reverse=True):
        slug = page.parent.name
        text = page.read_text(encoding="utf-8")
        title = first_match(r"<h1[^>]*>(.*?)</h1>", text, slug)
        topic = infer_topic(title, slug)
        papers = extract_papers(slug, text)
        result.append(
            {
                "slug": slug,
                "date": infer_date(slug),
                "title": title,
                "topic": topic,
                "cardTitle": extract_card_title(slug, text, topic),
                "kicker": extract_kicker(text, topic, papers),
                "frontier": extract_frontier_observation(text),
                "url": f"briefings/{slug}/",
                "papers": papers,
            }
        )
    return result


def default_state_path() -> pathlib.Path:
    override = os.getenv("RESEARCH_BRIEFINGS_READING_STATE")
    if override:
        return pathlib.Path(override)
    if DEFAULT_RESEARCH_WORKBENCH_STATE.exists():
        return DEFAULT_RESEARCH_WORKBENCH_STATE
    return LEGACY_ONEDRIVE_STATE


def load_public_state_snapshot(state_path: pathlib.Path | None) -> dict:
    """Return a privacy-safe reading-state fallback for static dashboard rendering."""
    if not state_path or not state_path.exists():
        return {}
    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    result: dict[str, dict] = {}
    for paper_id, state in (raw.get("papers") or {}).items():
        if not isinstance(state, dict):
            continue
        decision = state.get("decision") or "open"
        if decision == "open":
            continue
        archived = bool(
            state.get("shareUrl")
            or state.get("conversationUrl")
            or state.get("transcript")
            or state.get("transcriptStatus")
        )
        result[paper_id] = {
            "decision": decision,
            "star": decision == "important",
            "updatedAt": state.get("updatedAt") or "",
            "transcriptStatus": state.get("transcriptStatus") or "",
            "archived": archived,
        }
    return result


def build_html(data: list[dict], state_mode: str = "public", state_path: pathlib.Path | None = None) -> str:
    index_path = ROOT / "index.html"
    template = index_path.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    state_snapshot = load_public_state_snapshot(state_path) if state_mode == "local" else {}
    public_state = json.dumps(state_snapshot, ensure_ascii=False, separators=(",", ":"))
    projects = "\n".join(
        [
            "const PROJECTS = {",
            *[
                f"  {day}: {{ name: 'Paper Reading', url: '{COMMON_CHATGPT_PROJECT}' }},"
                for day in (1, 2, 3, 4, 5, 6)
            ],
            f"  0: {{ name: 'Paper Reading', url: '{COMMON_CHATGPT_PROJECT}' }}",
            "};",
        ]
    )
    template = re.sub(
        r"const BRIEFINGS = \[.*?\];\s*const PROJECTS = \{.*?\n\};(?:\s*const PUBLIC_READING_STATE = \{.*?\};)?",
        f"const BRIEFINGS = {payload};\n{projects}\nconst PUBLIC_READING_STATE = {public_state};",
        template,
        count=1,
        flags=re.S,
    )
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    template = re.sub(r"Generated \d{4}-\d{2}-\d{2} \d{2}:\d{2}", f"Generated {generated}", template, count=1)
    return template


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the research briefings dashboard.")
    parser.add_argument(
        "--state-mode",
        choices=("public", "local"),
        default=os.getenv("RESEARCH_BRIEFINGS_STATE_MODE", "public"),
        help="public omits personal reading state; local embeds a sanitized fallback snapshot.",
    )
    parser.add_argument(
        "--state-path",
        default=os.getenv("RESEARCH_BRIEFINGS_READING_STATE", ""),
        help="Optional reading-state.json path used when --state-mode local.",
    )
    args = parser.parse_args()
    data = load_briefings()
    state_path = pathlib.Path(args.state_path) if args.state_path else default_state_path()
    (ROOT / "index.html").write_text(build_html(data, args.state_mode, state_path), encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    embedded = len(load_public_state_snapshot(state_path)) if args.state_mode == "local" else 0
    print(
        f"wrote index.html with {len(data)} briefings and {sum(len(b['papers']) for b in data)} papers; "
        f"state_mode={args.state_mode}; embedded_state={embedded}"
    )


if __name__ == "__main__":
    main()
