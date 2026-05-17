import argparse
import json
import pathlib
import re
import sys

import build_dashboard


ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMON_CHATGPT_PROJECT = "https://chatgpt.com/g/g-p-69f2d27eda0c8191ba40e9e8d36855ed-du-lun-wen/project"
PRIVATE_PATTERNS = [
    r"data-rb-field=[\"']conversationUrl[\"']",
    r"data-rb-field=[\"']transcript[\"']",
    r"data-rb-action=[\"']shareHint[\"']",
    r"Transcripts[/\\]",
    r"OneDrive[/\\]",
    r"C:\\Users\\",
    r"E:\\Git Repo\\Research\\Transcripts",
]


def load_briefing(slug: str) -> dict:
    for item in build_dashboard.load_briefings():
        if item["slug"] == slug:
            return item
    raise RuntimeError(f"Slug not found in parsed briefings: {slug}")


def validate_slug(slug: str) -> dict:
    page = ROOT / "briefings" / slug / "index.html"
    index = ROOT / "index.html"
    errors: list[str] = []
    if not page.exists():
        errors.append(f"missing page: {page}")
        return {"ok": False, "slug": slug, "errors": errors}

    html = page.read_text(encoding="utf-8")
    index_html = index.read_text(encoding="utf-8") if index.exists() else ""
    briefing = load_briefing(slug)

    if slug not in index_html:
        errors.append("dashboard index does not contain slug")
    if not re.search(r"<h1[^>]*>.*?</h1>", html, flags=re.I | re.S):
        errors.append("missing h1")
    for heading in ("Read Now", "Watchlist"):
        if not re.search(rf"<h2[^>]*>\s*{re.escape(heading)}\s*</h2>", html, flags=re.I | re.S):
            errors.append(f"missing section: {heading}")
    if "research-briefing-reading-widget:start" not in html:
        errors.append("missing reading widget")
    if "data-rb-field=\"shareUrl\"" not in html:
        errors.append("missing ChatGPT record link field")
    if "data-rb-field=\"userNote\"" not in html:
        errors.append("missing user note field")
    if "researchBriefings.v2." not in html:
        errors.append("missing localStorage state namespace")
    if "parseChatGptRecordUrl" not in html:
        errors.append("missing ChatGPT share/conversation parser")
    if COMMON_CHATGPT_PROJECT not in html:
        errors.append("missing unified ChatGPT reading project URL")
    if 'class="rb-console-back"' not in html or 'href="../../"' not in html:
        errors.append("missing console back link")
    if "function buildReadingStarter(paper)" not in html:
        errors.append("missing first-pass reading starter")
    if "await copyReadingStarter(paper, true);" not in html:
        errors.append("start reading does not copy the reading starter")
    if "copyPrompt" in html or 'data-rb-action="copy"' in html or "复制 Prompt" in html:
        errors.append("old copy prompt control still present")
    for phrase in ("带我读这篇论文", "第一轮价值扫描", "默认目的：每日论文阅读学习"):
        if phrase not in html:
            errors.append(f"reading starter missing phrase: {phrase}")

    papers = briefing.get("papers", [])
    if not papers:
        errors.append("no parsed papers")
    for paper in papers:
        paper_id = paper.get("id", "")
        if f'"id":"{paper_id}"' not in html and f'"id": "{paper_id}"' not in html:
            errors.append(f"paper id missing from widget payload: {paper_id}")
        if ":read-now:" in paper_id or ":watchlist:" in paper_id:
            errors.append(f"non-canonical paper id: {paper_id}")
        if not (":read:" in paper_id or ":watch:" in paper_id):
            errors.append(f"paper id missing canonical section key: {paper_id}")

    for pattern in PRIVATE_PATTERNS:
        if re.search(pattern, html, flags=re.I):
            errors.append(f"private or deprecated visible field matched: {pattern}")

    state_match = re.search(r"const PUBLIC_READING_STATE = (\{.*?\});", index_html, flags=re.S)
    if not state_match:
        errors.append("missing public reading state declaration")
    else:
        try:
            public_state = json.loads(state_match.group(1))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid public reading state JSON: {exc}")
            public_state = {}
        if public_state:
            errors.append("public dashboard must not embed personal reading state; rebuild with --state-mode public")
        for private_key in ("shareUrl", "conversationUrl", "userNote", "transcript", "transcriptPath"):
            if private_key in state_match.group(1):
                errors.append(f"public reading state contains private key: {private_key}")
    if "Array.from({ length: 6 }" not in index_html:
        errors.append("dashboard Week Rail should render Monday-Saturday only")
    if ".task-cell.archived::after" not in index_html or ".watch-dot.archived" not in index_html:
        errors.append("dashboard missing archived paper markers")

    return {
        "ok": not errors,
        "slug": slug,
        "papers": len(papers),
        "dashboard": "ok" if slug in index_html else "missing",
        "readerControls": "ok" if "research-briefing-reading-widget:start" in html else "missing",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public briefing artifacts after publish.")
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()

    result = validate_slug(args.slug)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
