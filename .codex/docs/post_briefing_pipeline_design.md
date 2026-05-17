# Post-Briefing Pipeline Design

## 目标

briefing markdown 一旦生成，后续机械链路应由 Python pipeline 完成，不再依赖 Codex 手工改 HTML 或 Dashboard。

当前入口：

```powershell
python E:\Git Repo\Research\.codex\tools\publish_daily_briefing_pipeline.py "<briefing_file>"
```

当前过渡入口：

```powershell
python E:\Git Repo\Research\.codex\tools\publish_briefing_page.py "<briefing_file>"
```

## 脚本化范围

| 阶段 | 是否脚本化 | 原因 |
|---|---:|---|
| 主题判断 | 否 | 需要结合日期、轮转规则和上下文 |
| 网络检索和论文筛选 | 否 | 需要语义判断和 novelty 判断 |
| 写 briefing markdown | 否 | 需要中文综合表达 |
| markdown 到公开 HTML | 是 | 机械转换，可测试 |
| reader controls 注入 | 是 | 必须稳定，不能手工改 HTML |
| canonical paper id 生成 | 是 | 状态主键必须稳定 |
| Dashboard 数据抽取和 rebuild | 是 | 纯结构化处理 |
| public/private 泄露检查 | 是 | 正则和结构检查优先 |
| public repo commit / push | 是 | 标准 git 操作 |
| 手机端投递 | 是 | 标准 webhook / URL delivery |
| OneDrive event / transcript intake | 另一个脚本链路 | 不属于公开发布；由私有 watcher 处理 |

## 建议模块

第一版已实现：

```text
E:\Git Repo\Research\.codex\tools\publish_daily_briefing_pipeline.py
E:\Git Repo\Research\.codex\tools\export_reading_local_web.py
E:\Git Repo\Research\.codex\tools\local_reading_sync.js
E:\Git Repo\Research\.codex\tools\process_reading_events.py
E:\Git Repo\research-briefings\tools\inject_reader_controls.py
E:\Git Repo\research-briefings\tools\validate_public_artifacts.py
```

其中 `publish_daily_briefing_pipeline.py` 负责编排；public repo 两个脚本分别负责 reader 控件注入和公开产物验收；local web exporter 和 watcher 负责私有可写层。

### 1. `render_public_html`

输入：

```text
E:\Git Repo\Research\Briefings\<slug>.md
```

输出：

```text
E:\Git Repo\research-briefings\briefings\<slug>\index.html
```

要求：

- 保留 `<h1>`。
- 保留 `Read Now` 和 `Watchlist` heading。
- 论文标题必须是可点击外部 source link。
- 不写入私有路径和 transcript 内容。

### 2. `extract_paper_targets`

输入：公开 HTML 或 markdown。

输出：结构化 paper list。

字段：

```json
{
  "briefingSlug": "slug",
  "section": "read",
  "index": 1,
  "title": "Paper title",
  "url": "https://...",
  "paperId": "slug:read:1:https://..."
}
```

规则：

- `Read Now` section key 是 `read`。
- `Watchlist` section key 是 `watch`。
- 不使用 `read-now` 或 `watchlist` 作为 paper id segment。

### 3. `inject_reader_controls`

输入：

```text
briefings/<slug>/index.html
paper targets
```

输出：带 V1 reader panel 的同一 HTML。

每篇论文必须有：

- `?`
- `不读`
- `待读`
- `开始读`
- `简单 pass`
- `正常读`
- `重要`
- `复制 Prompt`
- `ChatGPT share 链接`
- `你的简短评语`

禁止恢复：

- GPT conversation URL 输入框。
- transcript 大文本框。
- `share 可自动归档`按钮。

### 4. `build_dashboard`

当前已有：

```powershell
python E:\Git Repo\research-briefings\tools\build_dashboard.py
```

目标：

- 抽取所有 `briefings/*/index.html`。
- 更新 `index.html` 中的 `BRIEFINGS`。
- 保持 UI 模板稳定。

后续建议：

- 将 `index.html` 自模板模式拆为 `tools/templates/dashboard.html`。

### 5. `validate_public_artifacts`

必须检查：

- 新 slug 存在于 Dashboard data。
- 新页面有 `Read Now` / `Watchlist`。
- 每篇论文有 canonical `paperId`。
- 每篇论文有 reader controls。
- public repo 不含以下私有内容：
  - `Transcripts/`
  - `OneDrive`
  - `conversationUrl`
  - transcript full text
  - local absolute private state paths
- overview 和新 briefing 页是 UTF-8。

建议返回 machine-readable JSON：

```json
{
  "ok": true,
  "slug": "slug",
  "dashboard": "ok",
  "readerControls": "ok",
  "privateLeakage": "ok",
  "errors": []
}
```

### 6. `push_public_repo`

输入：允许提交的 public paths。

允许：

```text
.nojekyll
index.html
briefings/<slug>/index.html
tools/build_dashboard.py
tools/templates/*
```

默认不提交：

```text
.codex/planning/*
private-state/*
transcripts/*
```

### 7. `deliver_mobile_url`

发送内容应短：

```text
今日主题：<topic>
Dashboard: <dashboard URL>
Briefing: <today URL>
```

不要发送内部验收表。

### 8. `emit_run_summary`

成功时给 Codex / 用户：

```text
今日主题：
dashboard URL：
today briefing URL：
```

失败时：

```text
blocked at：
detail：
```

## Pipeline 顺序

```text
Briefings/<slug>.md
-> render_public_html
-> extract_paper_targets
-> inject_reader_controls
-> build_dashboard
-> validate_public_artifacts
-> push_public_repo
-> deliver_mobile_url
-> emit_run_summary
```

任何一步失败都应 fail closed，不继续后续发布或投递。

## 与私有同步链路的关系

公开 pipeline 不处理 transcript。私有同步另走：

```text
OneDrive local web
-> per-paper event files
-> host watcher
-> transcript intake
-> transcript extraction
-> private state
-> sanitized public summary
```

public repo 未来可以消费 sanitized public summary，但不能成为私有状态写入端。

## Local Web Export

导出 OneDrive/local web：

```powershell
python E:\Git Repo\Research\.codex\tools\export_reading_local_web.py --sync-root "<OneDrive>\ResearchReadingSync"
```

或在每日发布 pipeline 中附加：

```powershell
python E:\Git Repo\Research\.codex\tools\publish_daily_briefing_pipeline.py "<briefing_file>" --local-sync-root "<OneDrive>\ResearchReadingSync"
```

导出结果：

```text
<sync-root>/web/
<sync-root>/inbox/pending/
<sync-root>/inbox/processing/
<sync-root>/inbox/done/
<sync-root>/inbox/failed/
<sync-root>/state/reading-state.json
<sync-root>/outbox/public-reading-summary.json
```

本地网页会注入 `assets/local_reading_sync.js`。用户在 local web 中修改论文状态时，事件先进入浏览器 pending queue；选择同步目录后写入 `<sync-root>/inbox/pending/*.json`。如果浏览器不支持目录写入，可以下载 pending events JSON 手动导入。

## Host Watcher

消费 pending events：

```powershell
python E:\Git Repo\Research\.codex\tools\process_reading_events.py --sync-root "<OneDrive>\ResearchReadingSync"
```

第一版 watcher 做：

- 校验 event schema。
- `pending -> processing -> done/failed`。
- 更新 `<sync-root>/state/reading-state.json`。
- 生成脱敏 `<sync-root>/outbox/public-reading-summary.json`。

第一版 watcher 还不抓真实 ChatGPT transcript；有 `shareUrl` 且状态为 `pass/read/important` 时，先标记 `transcriptStatus = pending`。
