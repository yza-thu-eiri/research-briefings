# Daily Briefing Dashboard Integration Contract

## 目的

这份文档定义每日 briefing 生成系统与 `research-briefings` Dashboard V1 的接口契约。后续自动化、发布脚本、页面生成器和 UI 迭代都应以这里为准，避免再次出现阅读记录失配、Dashboard 无法解析、或新 briefing 页面缺少 reader 控件的问题。

## 给 Codex 的执行摘要

如果你是在每日自动化中读到本文件，请按下面的顺序判断，不要先读完整 UI 设计史：

1. 确认私有源文件：`E:\Git Repo\Research\Briefings\<date-topic>.md`。
2. 确认公开页面：`briefings/<slug>/index.html`。
3. 确认 Dashboard 数据：`tools/build_dashboard.py` 能把新页面写入 `index.html` 的 `BRIEFINGS`。
4. 确认 reader controls：每篇 Read Now / Watchlist 论文都有状态按钮、`ChatGPT share 链接`、`你的简短评语`。
5. 确认 public/private 边界：公开 repo 不保存 ChatGPT share、个人评语、transcript 全文或本地路径。
6. 成功时最终只向用户报告今日主题、Dashboard URL、今日 briefing URL；完整检查项留在脚本日志或失败报告中。

缺少第 3 项时，手机能打开单页但总览不会收纳当天内容。缺少第 4 项时，网页正文可以读，但阅读 console 没有完整接入。缺少第 5 项时，可能泄露私有阅读数据。

## 自动化分工目标

长期目标是：Codex 只负责 briefing 内容生成和异常判断；briefing markdown 完成后，所有机械发布工作由 Python 脚本接管。

| 阶段 | 推荐执行者 | 说明 |
|---|---|---|
| 选题、检索、论文价值判断 | Codex | 需要语义判断和外部信息综合 |
| 写 `Briefings/<slug>.md` | Codex | 需要生成中文、移动端可读 briefing |
| 渲染公开 HTML | Python | 纯机械转换，应脚本化 |
| 注入 reader controls | Python | 必须稳定、可测试，不应手工改 HTML |
| 刷新 Dashboard | Python | `tools/build_dashboard.py` 或后续统一 build pipeline |
| public/private 泄露检查 | Python first, Codex on failure | 正则/结构检查脚本优先，异常再交给 Codex |
| commit / push / delivery | Python | 成功时只返回 URL；失败时返回错误 |
| transcript intake / extraction | 主机 watcher / Python | 不属于 public Pages 发布；消费 OneDrive event files |

因此，后续工程化优先补齐一个“post-briefing publish pipeline”，而不是继续让每日 Codex 自动化理解 UI 细节。

脚本拆分和接口设计见：

```text
E:\Git Repo\research-briefings\.codex\docs\post_briefing_pipeline_design.md
```

## 参与仓库

私有研究库：

```text
E:\Git Repo\Research
```

公开 Pages 仓库：

```text
E:\Git Repo\research-briefings
https://github.com/yza-thu-eiri/research-briefings
```

公开页面 URL 规则：

```text
https://yza-thu-eiri.github.io/research-briefings/
https://yza-thu-eiri.github.io/research-briefings/briefings/<slug>/
```

## 当前发布链路

私有 Research 自动化运行结束后调用：

```powershell
python .codex/tools/publish_briefing_page.py "<briefing_file>"
```

该脚本当前做三件事：

1. 把 `Briefings/<briefing_file>.md` 渲染为公开 repo 下的：

```text
briefings/<slug>/index.html
```

2. 如果公开 repo 存在：

```text
tools/build_dashboard.py
```

则自动执行它，刷新公开 repo 的 `index.html` Dashboard。

3. 提交并推送公开 repo 中：

```text
.nojekyll
index.html
briefings/<slug>/index.html
```

这意味着：每日系统已经知道要刷新 Dashboard，但它还没有显式知道 reader 控件的完整模板契约。V1 收尾后，下一步工程化必须补齐这一点。

当前 V1 发布脚本入口是：

```powershell
python .codex/tools/publish_daily_briefing_pipeline.py "<briefing_file>"
```

该脚本内部应完成 HTML render、reader injection、Dashboard rebuild、validation、public push、mobile delivery，并把详细检查写入日志。Codex 不应常规手工执行这些子步骤。

旧入口 `publish_briefing_page.py` 只作为回退路径；它不能完整保证 reader controls / Dashboard V1 接入。

## Producer / Consumer 边界

每日 briefing 生成链路要把这套网页当成两个明确的消费者来服务：

| 角色 | 位置 | 消费什么 | 不能假设什么 |
|---|---|---|---|
| Briefing 页面 | `briefings/<slug>/index.html` | 已渲染的正文、Read Now / Watchlist 论文链接、reader 控件脚本 | 不能假设用户只在当天阅读；状态必须能跨天保存 |
| Dashboard 总览 | `index.html` + `tools/build_dashboard.py` | 每个 briefing 页里的标题、主题、论文链接、frontier 摘要 | 不能假设人工会手动补数据；新 briefing 必须可自动解析 |
| 浏览器本地状态 | `localStorage` | `researchBriefings.v2.<paper-id>` | 不能随意改 paper id，否则旧阅读记录会看起来消失 |
| 发布自动化 | Research 私有 repo 的 publish/render 脚本 | 公开 repo 的页面结构和生成命令 | 不能只生成普通 HTML；还要满足 V1 reader 接入 |

因此，后续每日生成端必须同时满足两类输出：

1. 机器可解析输出：Dashboard 能从 HTML 中稳定抽取日期、主题、标题、Read Now、Watchlist、论文链接。
2. 用户可记录输出：每篇论文下方都有 V1 reader panel，且 panel 使用 canonical paper id 写入 localStorage。

## 多端数据分层

参考私有 Research 规划：

```text
E:\Git Repo\Research\.codex\planning\2026-05-15-reading-transcript-sync\
```

V1 之后要把同一套 briefing 分成四层数据粒度：

| 层 | 位置 | 数据 | 写入者 | 是否可公开 |
|---|---|---|---|---:|
| 公开网页层 | GitHub Pages / `research-briefings` | briefing 正文、论文链接、脱敏进度、Dashboard UI | 发布脚本 | 是 |
| 浏览器临时层 | `localStorage` | 当前浏览器的阅读状态、share URL、user note | 用户浏览器 | 否，不可依赖跨设备 |
| 私有同步层 | OneDrive local web / event files | per-paper reading event、ChatGPT share/conversation URL、个人评语 | 本地可写网页或手动导入 | 否 |
| 主机处理层 | Research vault / transcript intake | transcript 原文、extraction、归档状态、脱敏 summary | 主机 watcher / Codex | 否，只有脱敏 summary 可发布 |

当前 GitHub Pages 只应承担“手机端可访问”和“公开只读展示”。后续如果要实现跨设备同步，应由 OneDrive 本地可写版本写入 event files，再由主机 watcher 消费。不要把私有状态直接写入 public repo。

建议 event 粒度是 per-paper，而不是整天一个大 JSON：

```json
{
  "briefingSlug": "2026-05-14-Acceleration-long-context-systems-network-first-briefing-zh",
  "paperId": "<slug>:read:<index>:<paper-url>",
  "paperTitle": "Paper title",
  "topic": "Acceleration / Long-Context",
  "decision": "read",
  "shareUrl": "https://chatgpt.com/share/...",
  "userNote": "short private comment",
  "createdAt": "2026-05-15T10:30:00+08:00"
}
```

该 event 可以进入 OneDrive `inbox/pending/`，但不应进入 GitHub Pages 仓库。

## 每日生成端必须知道的 V1 设计

生成系统不需要理解所有视觉细节，但必须知道这些不可破坏的接口：

1. 主题按周几固定，Dashboard 会按日期推断主题；slug、标题和页面正文应保持主题一致。
2. `Read Now` 是主任务，决定每日 level；`Watchlist` 是 bonus，不拖累主等级。
3. `skip` 是一种完成判断，不要求 share 链接；`pass`、`read`、`important` 是读后状态，应提醒补 `shareUrl`。
4. `important` 不是每天必须出现的目标；它是额外高价值信号。
5. `Reading Activity` 按用户实际操作日期统计，不按 briefing 日期统计；因此 reader 控件写入 `events` 很重要。
6. 单篇论文的读后输入只保留 `ChatGPT share 链接` 和 `你的简短评语`；不要恢复 transcript 大框或 GPT conversation URL 输入框。

## 新增 Daily Briefing 的完整接入定义

新增一天 briefing 只有同时满足以下条件，才算已经接入 Dashboard V1：

1. `briefings/<slug>/index.html` 已存在。
2. 页面有可解析的 `<h1>`、`Read Now`、`Watchlist` 结构。
3. 每个 Read Now / Watchlist 论文链接都能生成 canonical paper id。
4. 每篇论文后有 V1 reader panel。
5. `python tools\build_dashboard.py` 已执行成功。
6. `index.html` 的 `BRIEFINGS` 数据里包含新 slug。
7. 新 briefing 页面和总览页都能打开。

缺少第 4 项时，只能算“公开正文已发布”，不能算“阅读追踪系统已接入”。

脚本内部应把结果分级记录：

| 结果 | 含义 |
|---|---|
| `source generated` | 私有 markdown 已生成 |
| `public page published` | 公开单页已生成并推送 |
| `dashboard refreshed` | 总览页已包含新 briefing |
| `reader controls ready` | 新单页可记录状态，paper id 稳定 |
| `mobile delivered` | URL 已投递到手机端渠道 |
| `private sync not run` | 正常状态；transcript / OneDrive watcher 不属于每日公开发布必做项 |

成功时这些结果不需要全部贴给用户；只要给出 Dashboard URL 和今日 briefing URL。失败或部分成功时，再暴露最短阻塞项。

## 自动化失败与跳过规则

每日自动化可以 fail closed，但失败原因必须说清楚：

| 失败点 | 是否继续发布 | 说明 |
|---|---:|---|
| 无法写公开 repo | 否 | 无法更新 Pages，不应伪报已发布 |
| `build_dashboard.py` 失败 | 否 | 总览可能缺新数据，应停止并报告 |
| 新页面没有 reader panel | 不应视为完整成功 | 可报告正文已发布，但 V1 阅读追踪未完成 |
| Git push 失败 | 否 | 远端页面不会更新 |
| WeCom / webhook 失败 | 可视任务策略而定 | 页面发布成功和投递失败应分开报告 |

自动化最终回复建议保留这几行，方便后续排障：

```text
briefing file path:
public webpage URL:
dashboard refresh result:
reader controls result:
git commit/push result:
delivery result:
any failure or skipped step:
```

## Dashboard 数据解析契约

`tools/build_dashboard.py` 从每个公开页面读取：

```text
briefings/*/index.html
```

并抽取以下字段：

| 字段 | 来源 | 要求 |
|---|---|---|
| `slug` | `briefings/<slug>/index.html` 的目录名 | 必须稳定 |
| `date` | slug 开头的 `YYYY-MM-DD` | 必须存在 |
| `title` | 页面第一个 `<h1>` | 必须存在 |
| `topic` | `<h1>` 或 slug 推断 | 应与周几主题一致 |
| `cardTitle` | override 或 core points | 可选但建议短标题 |
| `kicker` | core points + Read Now 论文 | 用于总览卡片 |
| `frontier` | `前沿变化观察` / `Key Patterns` / `What I Learned` | 可选 |
| `papers` | `Read Now` / `Watchlist` section 中的论文链接 | Dashboard 核心 |

## Briefing HTML 最小结构

为保证 Dashboard 可解析，公开 briefing 页必须至少包含：

```html
<h1>今日主题：...</h1>

<h2>Read Now</h2>
<!-- 3-5 papers, each with clickable external paper link -->

<h2>Watchlist</h2>
<!-- optional papers, each with clickable external paper link -->
```

兼容的论文链接域名当前包括：

```text
arxiv.org
microsoft.com
aclanthology.org
openreview.net
github.com
doi.org
```

如果新来源需要进入 Dashboard，应先更新 `tools/build_dashboard.py` 的链接白名单。

## Paper ID 契约

Paper id 是 localStorage 阅读记录的主键，必须保持稳定。

当前 canonical 格式：

```text
<briefing-slug>:read:<index>:<paper-url>
<briefing-slug>:watch:<index>:<paper-url>
```

禁止改成：

```text
<briefing-slug>:read-now:<index>:<paper-url>
<briefing-slug>:watchlist:<index>:<paper-url>
```

也不要在 section key 后插入空格。

原因：浏览器端状态存在：

```text
researchBriefings.v2.<paper-id>
```

paper id 变化会让旧记录看起来“被清空”。总览页已有 `stateKeyCandidates()` 兼容迁移，但生成器必须继续输出 canonical id。

## 阅读状态契约

状态值：

| decision | 含义 | 是否完成判断 | 是否要求 share |
|---|---|---:|---:|
| `open` | 未选择 | 否 | 否 |
| `skip` | 不读 | 是 | 否 |
| `queue` | 待读 | 否 | 否 |
| `reading` | 阅读中 | 否 | 可先填 |
| `pass` | 读后简单 pass | 是 | 是 |
| `read` | 读后正常读 | 是 | 是 |
| `important` | 读后重要 | 是 | 是 |

V1 UI 主动编辑：

```js
decision
shareUrl
userNote
startedAt
updatedAt
events
```

兼容保留但不再作为 UI 主入口：

```js
conversationUrl
conversationId
projectId
transcript
readingNote
```

## 单篇 Briefing Reader 控件契约

每篇论文应有一个 reader panel，最小 UI 是：

1. 状态按钮：
   - `?`
   - `不读`
   - `待读`
   - `开始读`
   - `简单 pass`
   - `正常读`
   - `重要`

2. 工具按钮：
   - `复制 Prompt`

3. 读后记录区只保留：
   - `ChatGPT share 链接`
   - `你的简短评语`

不应恢复：

- GPT 对话链接输入框。
- Transcript 大文本框。
- `share 可自动归档`按钮。

## 当前工程化缺口

这是 V1 最重要的后续风险：

公开 repo 当前只有：

```text
tools/build_dashboard.py
```

它负责重建总览页，但不负责重建或注入 `briefings/<slug>/index.html` 的 reader 控件。

目前 12 个既有 briefing 页已经批量更新为 V1 reader UI；但未来每日新生成的 briefing 是否自动带有同样 reader 控件，取决于私有 Research 中：

```text
.codex/tools/render_briefing_formats.py
```

和：

```text
.codex/tools/publish_briefing_page.py
```

因此下一阶段必须新增或改造以下其一：

### 推荐方案 A：公开 repo 提供 reader 注入器

新增：

```text
tools/inject_reader_controls.py
```

职责：

1. 扫描 `briefings/*/index.html`。
2. 识别每个 Read Now / Watchlist paper link。
3. 按 canonical paper id 注入 V1 reader panel。
4. 保持旧 localStorage key 不变。

然后修改 `tools/build_dashboard.py` 或发布脚本，使每次发布后执行：

```powershell
python tools\inject_reader_controls.py
python tools\build_dashboard.py
```

### 推荐方案 B：私有 Research 渲染器直接输出 reader 控件

修改：

```text
E:\Git Repo\Research\.codex\tools\render_briefing_formats.py
```

让它在生成公开 HTML 时直接包含 V1 reader panel 和脚本。

优点：发布一次成型。

风险：私有 repo 的渲染器要理解公开 Dashboard 的 localStorage contract。

### 不建议方案

继续手工或临时脚本批量替换 `briefings/*/index.html`。这会导致下一次 daily automation 新增页面时 UI 不一致。

## Dashboard 生成器契约

`tools/build_dashboard.py` 当前是自模板模式：

1. 读取现有 `index.html`。
2. 替换 `const BRIEFINGS = ...`。
3. 替换 `Generated YYYY-MM-DD HH:MM`。
4. 写回 `index.html`。

后续工程化应改为：

```text
tools/templates/dashboard.html
tools/build_dashboard.py
```

不要继续让 `index.html` 同时充当模板和产物。

## 自动化发布后的检查项

每日发布成功后，至少检查：

```powershell
python tools\build_dashboard.py
```

并验证：

```text
index.html contains the new briefing in BRIEFINGS
new paper ids use :read:<index>: or :watch:<index>:
new briefing page has reader controls
overview page loads
new briefing URL loads
```

如果新 briefing 没有 reader 控件，不要视为 V1 完整发布。

Codex 友好的检查命令示例：

```powershell
python tools\build_dashboard.py
Select-String -Path index.html -Pattern "<slug>"
Select-String -Path "briefings\<slug>\index.html" -Pattern "data-rb-action|researchBriefings.v2|ChatGPT share"
```

如果检查命令因为当前 shell quoting 失败，不要重复同一个命令；换成更简单的 `Select-String` 或小段 Python 检查。

## 给自动化/后续 Agent 的最短提示

后续 Agent 若需要维护每日 briefing 发布，请先读：

```text
E:\Git Repo\research-briefings\.codex\docs\daily_briefing_dashboard_integration_contract.md
E:\Git Repo\research-briefings\.codex\docs\research_briefings_dashboard_v1.md
```

然后再修改：

```text
E:\Git Repo\Research\.codex\tools\publish_briefing_page.py
E:\Git Repo\Research\.codex\tools\render_briefing_formats.py
E:\Git Repo\research-briefings\tools\build_dashboard.py
```

不要只看 UI 截图做改动。

## 2026-05-17 发布边界更新

每日发布流水线必须使用 public build：

```powershell
python tools\inject_reader_controls.py --slug <slug>
python tools\build_dashboard.py --state-mode public
python tools\validate_public_artifacts.py --slug <slug>
```

规则：
- GitHub Pages 版本不得嵌入个人阅读状态，`PUBLIC_READING_STATE` 必须为空对象 `{}`。
- 本地/LAN 版本如需离线兜底显示，可使用 `python tools\build_dashboard.py --state-mode local`，它只嵌入脱敏字段：`decision`、`star`、`updatedAt`、`transcriptStatus`、`archived`。
- 发布脚本 `E:\Git Repo\Research\.codex\tools\publish_daily_briefing_pipeline.py` 已固定调用 `--state-mode public`。
- 新 briefing 页必须有 reader controls、Console 返回入口、统一 ChatGPT 论文阅读项目、share/conversation URL 兼容解析。
- `开始读` 的行为是复制第一轮价值扫描启动词并打开统一 ChatGPT 项目；不要恢复独立的 `复制 Prompt` 按钮。
