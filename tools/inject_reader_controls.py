import argparse
import json
import pathlib
import re
import sys

import build_dashboard


ROOT = pathlib.Path(__file__).resolve().parents[1]
START = "<!-- research-briefing-reading-widget:start -->"
END = "<!-- research-briefing-reading-widget:end -->"
COMMON_CHATGPT_PROJECT = "https://chatgpt.com/g/g-p-69f2d27eda0c8191ba40e9e8d36855ed-du-lun-wen/project"


def widget_pattern() -> re.Pattern:
    return re.compile(rf"\n*{re.escape(START)}.*?{re.escape(END)}\n*", flags=re.S)


def find_reference_widget(root: pathlib.Path, preferred_slug: str | None = None) -> str:
    pages = sorted((root / "briefings").glob("*/index.html"), reverse=True)
    if preferred_slug:
      pages = sorted(pages, key=lambda p: p.parent.name != preferred_slug)
    for page in pages:
        text = page.read_text(encoding="utf-8")
        match = widget_pattern().search(text)
        if match:
            return match.group(0).strip()
    raise RuntimeError("No existing reading widget block found in briefings/*/index.html")


def briefing_payload(slug: str) -> dict:
    for item in build_dashboard.load_briefings():
        if item["slug"] == slug:
            return item
    raise RuntimeError(f"Cannot build BRIEFING payload for slug: {slug}")


def replace_payload(widget: str, payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    replaced, count = re.subn(
        r"const BRIEFING = .*?;\s*const PROJECTS =",
        f"const BRIEFING = {encoded};\n  const PROJECTS =",
        widget,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("Cannot replace BRIEFING payload in reading widget template")
    return replaced


def normalize_widget(widget: str) -> str:
    projects = "\n".join(
        [
            "const PROJECTS = {",
            *[
                f"    {day}: {{ name: 'Paper Reading', url: '{COMMON_CHATGPT_PROJECT}' }},"
                for day in (1, 2, 3, 4, 5, 6)
            ],
            f"    0: {{ name: 'Paper Reading', url: '{COMMON_CHATGPT_PROJECT}' }}",
            "  };",
        ]
    )
    widget = re.sub(r"const PROJECTS = \{.*?\n  \};", projects, widget, count=1, flags=re.S)
    if ".rb-console-back" not in widget:
        widget = widget.replace(
            "@media (max-width: 1260px) { .rb-side-index { position: static; width: auto; max-height: none; margin: 16px auto; } }",
            """.rb-console-back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  margin-bottom: 8px;
  border: 1px solid rgba(0,137,167,.24);
  border-radius: 7px;
  padding: 7px 8px;
  background: #f7fcfd;
  color: #006f86;
  text-decoration: none;
  font-size: 12px;
  font-weight: 900;
}
.rb-console-back:hover { background: #eaf6f9; }
@media (max-width: 1260px) { .rb-side-index { position: static; width: auto; max-height: none; margin: 16px auto; } }""",
        )
    widget = re.sub(
        r"function buildPrompt\(paper\) \{.*?\n  function parseConversationUrl",
        """function buildReadingStarter(paper) {
    const link = paper.url || 'no link provided';
    return `带我读这篇论文，先做第一轮价值扫描，不要精读全文：

标题：【${paper.title}】
链接 / PDF：【${link}】

默认目的：每日论文阅读学习。
请先判断值不值得继续读、核心机制是什么、证据强不强、主要漏洞和阅读路径。`;
  }
  async function copyReadingStarter(paper, silent = false) {
    const text = buildReadingStarter(paper);
    try {
      await navigator.clipboard.writeText(text);
      if (!silent) alert('阅读启动词已复制');
      return true;
    } catch (error) {
      if (!silent) window.prompt('复制失败，请手动复制阅读启动词', text);
      return false;
    }
  }
  function parseConversationUrl""",
        widget,
        count=1,
        flags=re.S,
    )
    starter_js = """function buildReadingStarter(paper) {
    const link = paper.url || 'no link provided';
    return `带我读这篇论文，先做第一轮价值扫描，不要精读全文：

标题：【${paper.title}】
链接 / PDF：【${link}】

默认目的：每日论文阅读学习。
请先判断值不值得继续读、核心机制是什么、证据强不强、主要漏洞和阅读路径。`;
  }
  function fallbackCopyText(text) {
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.left = '-9999px';
    area.style.top = '0';
    document.body.appendChild(area);
    area.focus();
    area.select();
    let ok = false;
    try { ok = document.execCommand('copy'); }
    catch (error) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }
  async function copyReadingStarter(paper, silent = false) {
    const text = buildReadingStarter(paper);
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        if (!silent) alert('阅读启动词已复制');
        return true;
      }
    } catch (error) {}
    const copied = fallbackCopyText(text);
    if (!copied && !silent) window.prompt('复制失败，请手动复制阅读启动词', text);
    if (copied && !silent) alert('阅读启动词已复制');
    return copied;
  }
  function parseConversationUrl"""
    widget = re.sub(
        r"function buildReadingStarter\(paper\) \{.*?\n  function parseConversationUrl",
        starter_js,
        widget,
        count=1,
        flags=re.S,
    )
    widget = re.sub(
        r"function parseConversationUrl\(value\) \{.*?\n  function draftFor",
        """function parseConversationUrl(value) {
    const match = value.match(/chatgpt\\.com\\/g\\/([^/]+)\\/c\\/([^/?#]+)/);
    return match ? { projectId: match[1], conversationId: match[2] } : null;
  }
  function parseShareUrl(value) {
    const match = value.match(/chatgpt\\.com\\/share\\/([^/?#]+)/);
    return match ? { shareId: match[1] } : null;
  }
  function parseChatGptRecordUrl(value) {
    const share = parseShareUrl(value);
    if (share) return { kind: 'share', ...share };
    const conversation = parseConversationUrl(value);
    if (conversation) return { kind: 'conversation', ...conversation };
    return null;
  }
  async function startReading(paper) {
    writeState(paper, { decision: 'reading', startedAt: readState(paper).startedAt || new Date().toISOString(), awaitingConversation: true });
    await copyReadingStarter(paper, true);
    window.open(projectFor().url, '_blank', 'noopener');
  }
  function setConversation(paper, value) {
    const trimmed = value.trim();
    if (!trimmed) {
      writeState(paper, { conversationUrl: '', projectId: '', conversationId: '', awaitingConversation: false });
      return;
    }
    const parsed = parseConversationUrl(trimmed);
    if (!parsed) {
      alert('This does not look like a ChatGPT /c/... conversation link');
      return;
    }
    writeState(paper, { conversationUrl: trimmed, projectId: parsed.projectId, conversationId: parsed.conversationId, awaitingConversation: false });
  }
  function setShare(paper, value) {
    const trimmed = value.trim();
    if (!trimmed) {
      writeState(paper, { shareUrl: '', shareId: '', conversationUrl: '', projectId: '', conversationId: '' });
      return;
    }
    const parsed = parseChatGptRecordUrl(trimmed);
    if (!parsed) {
      alert('This does not look like a ChatGPT share or /c/... conversation link');
      return;
    }
    const patch = parsed.kind === 'share'
      ? { shareUrl: trimmed, shareId: parsed.shareId, conversationUrl: '', projectId: '', conversationId: '', awaitingConversation: false }
      : { shareUrl: trimmed, shareId: '', conversationUrl: trimmed, projectId: parsed.projectId, conversationId: parsed.conversationId, awaitingConversation: false };
    writeState(paper, patch);
  }
  function draftFor""",
        widget,
        count=1,
        flags=re.S,
    )
    widget = re.sub(
        r"function saveRecord\(paper, panel\) \{.*?\n  function panelHtml",
        """function saveRecord(paper, panel) {
    const shareInput = panel.querySelector('[data-rb-field="shareUrl"]');
    const noteInput = panel.querySelector('[data-rb-field="userNote"]');
    const shareValue = shareInput ? shareInput.value.trim() : '';
    let parsed = null;
    if (shareValue) {
      parsed = parseChatGptRecordUrl(shareValue);
      if (!parsed) {
        alert('This does not look like a ChatGPT share or /c/... conversation link');
        return;
      }
    }
    const patch = shareValue
      ? (parsed.kind === 'share'
        ? { shareUrl: shareValue, shareId: parsed.shareId, conversationUrl: '', projectId: '', conversationId: '', awaitingConversation: false }
        : { shareUrl: shareValue, shareId: '', conversationUrl: shareValue, projectId: parsed.projectId, conversationId: parsed.conversationId, awaitingConversation: false })
      : { shareUrl: '', shareId: '', conversationUrl: '', projectId: '', conversationId: '' };
    patch.userNote = noteInput ? noteInput.value : '';
    writeState(paper, patch);
    recordDrafts.delete(paper.id);
    openRecordEditors.delete(paper.id);
    renderPanel(paper);
  }
  function panelHtml""",
        widget,
        count=1,
        flags=re.S,
    )
    widget = re.sub(
        r"const archiveLink = s\.shareUrl\n.*?\n    const draft = draftFor",
        """const archiveLink = s.shareUrl
      ? `<a class="rb-reader-link" href="${s.shareUrl}" target="_blank" rel="noopener">Open GPT record</a>`
      : (s.conversationUrl
        ? `<a class="rb-reader-link" href="${s.conversationUrl}" target="_blank" rel="noopener">Open GPT record</a>`
        : (s.transcript ? 'legacy transcript exists' : 'no GPT record'));
    const needsShare = ['pass', 'read', 'important'].includes(s.decision) && !s.shareUrl && !s.conversationUrl;
    const showRecord = ['reading', 'pass', 'read', 'important'].includes(s.decision);
    const recordOpen = showRecord && (openRecordEditors.has(paper.id) || needsShare || s.awaitingConversation);
    const recordSummary = s.shareUrl || s.conversationUrl || s.userNote
      ? `${(s.shareUrl || s.conversationUrl) ? 'GPT link saved' : 'GPT link missing'} - ${s.userNote ? 'note saved' : 'note missing'}`
      : 'no reading record yet';
    const draft = draftFor""",
        widget,
        count=1,
        flags=re.S,
    )
    widget = widget.replace(
        "${needsShare ? '<div class=\"rb-reader-reminder\">\\u5df2\\u5224\\u5b9a\\u8bfb\\u540e\\u7b49\\u7ea7\\uff0c\\u8bf7\\u8865 ChatGPT share \\u94fe\\u63a5\\u3002</div>' : ''}",
        "${needsShare ? '<div class=\"rb-reader-reminder\">Add a ChatGPT share or conversation link after grading.</div>' : ''}",
    )
    widget = widget.replace(
        'placeholder="\\u7c98\\u8d34 ChatGPT share \\u94fe\\u63a5\\uff1ahttps://chatgpt.com/share/..."',
        'placeholder="ChatGPT share or conversation link: https://chatgpt.com/share/... or https://chatgpt.com/g/.../c/..."',
    )
    widget = re.sub(
        r"\n\s*<div class=\"rb-reader-row\">\s*<span class=\"rb-reader-row-label\">\\u5de5\\u5177</span>\s*<button class=\"rb-reader-btn tool\" data-rb-action=\"copy\">\\u590d\\u5236 Prompt</button>\s*</div>",
        "",
        widget,
        flags=re.S,
    )
    widget = widget.replace("        if (action === 'copy') copyPrompt(paper);\n", "")
    if "rb-console-back" in widget and 'href="../../"' not in widget:
        widget = widget.replace(
            '<div class="rb-side-title">阅读进度</div>${paperHtml}<div class="rb-side-title">文档结构</div>${docs}`;',
            '<a class="rb-console-back" href="../../">Console</a><div class="rb-side-title">阅读进度</div>${paperHtml}<div class="rb-side-title">文档结构</div>${docs}`;',
        )
        widget = widget.replace(
            '<div class="rb-side-title">\\u9605\\u8bfb\\u8fdb\\u5ea6</div>${paperHtml}<div class="rb-side-title">\\u6587\\u6863\\u7ed3\\u6784</div>${docs}`;',
            '<a class="rb-console-back" href="../../">Console</a><div class="rb-side-title">\\u9605\\u8bfb\\u8fdb\\u5ea6</div>${paperHtml}<div class="rb-side-title">\\u6587\\u6863\\u7ed3\\u6784</div>${docs}`;',
        )
    return widget


def inject_widget(page: pathlib.Path, widget: str) -> None:
    html = page.read_text(encoding="utf-8")
    html = widget_pattern().sub("\n", html)
    if "</body>" in html:
        html = html.replace("</body>", f"\n\n{widget}\n\n</body>", 1)
    elif "</html>" in html:
        html = html.replace("</html>", f"\n\n{widget}\n\n</html>", 1)
    else:
        html = html.rstrip() + "\n\n" + widget + "\n"
    page.write_text(html, encoding="utf-8")


def inject_slug(slug: str, root: pathlib.Path = ROOT) -> pathlib.Path:
    page = root / "briefings" / slug / "index.html"
    if not page.exists():
        raise RuntimeError(f"Briefing page not found: {page}")
    payload = briefing_payload(slug)
    widget = normalize_widget(replace_payload(find_reference_widget(root, preferred_slug=slug), payload))
    inject_widget(page, widget)
    return page


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject the V1 reading widget into briefing pages.")
    parser.add_argument("--slug", help="Inject one briefing slug. Defaults to all pages.")
    args = parser.parse_args()

    if args.slug:
        pages = [inject_slug(args.slug)]
    else:
        pages = [inject_slug(page.parent.name) for page in sorted((ROOT / "briefings").glob("*/index.html"))]
    for page in pages:
        print(page)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[-] reader control injection failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
