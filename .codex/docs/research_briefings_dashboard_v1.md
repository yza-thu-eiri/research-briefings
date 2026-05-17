# Research Briefings Dashboard V1

## 定位

这个仓库的 V1 界面是一个“论文简报阅读追踪台”，不是普通文章索引页。它要解决四件事：

1. 快速看到每个固定主题的整体阅读状态。
2. 按日期查看 briefing 是否已处理、读了多少、是否有重要论文。
3. 进入单篇 briefing 后，按论文做“读不读、读后等级、share 归档、个人评语”的轻量记录。
4. 用实际阅读发生日期生成 Reading Activity，补读也能反映在真实阅读时间线上。

V1 可以认为 UI 设计第一版结束。后续迭代应优先保持当前信息架构，不要把控件重新堆回到单篇论文卡片里。

## 文件与生成链路

核心文件：

- `index.html`：总览页，也是当前 `tools/build_dashboard.py` 的版式模板。
- `tools/build_dashboard.py`：从 `briefings/*/index.html` 抽取数据，并替换 `index.html` 中的 `const BRIEFINGS = ...` 与生成时间。
- `briefings/*/index.html`：每个 briefing 的公开页面，包含单篇论文阅读控件。
- `.codex/docs/daily_briefing_dashboard_integration_contract.md`：每日 briefing 生成系统与公开 Dashboard 的接口契约。后续自动化和发布脚本必须先读这里。
- `.codex/planning/task_plan.md`、`.codex/planning/findings.md`、`.codex/planning/progress.md`：本轮设计和实现记录。

当前生成命令：

```powershell
python tools\build_dashboard.py
```

验证命令：

```powershell
python -m py_compile tools\build_dashboard.py
@'
const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf8');
for (const s of [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1])) new Function(s);
console.log('overview js ok');
'@ | node
```

本地预览：

```powershell
python -m http.server 8787
```

打开：

```text
http://127.0.0.1:8787/
```

注意：当前 `build_dashboard.py` 是“自模板”模式，会读取已有 `index.html` 作为模板再替换数据。因此修改总览 UI 时，要先改 `index.html`，再跑生成器确认模板不会覆盖改动。

每日 briefing 发布链路的额外接口约束见：

```text
.codex/docs/daily_briefing_dashboard_integration_contract.md
```

关键点：私有 Research 的 `publish_briefing_page.py` 已会调用公开 repo 的 `tools/build_dashboard.py` 刷新 Dashboard，但 V1 reader 控件还没有独立生成器。新增 daily briefing 若只生成普通公开 HTML，而没有 reader panel，则不算完整接入 V1。

跨端状态边界同样以 integration contract 为准：GitHub Pages 是公开只读层，适合手机端打开和 Dashboard 浏览；ChatGPT share 链接、个人评语、transcript 全文和本地路径不应写入 public repo。后续跨设备可写状态应走 OneDrive local web + per-paper event files + 主机 watcher，再由主机生成脱敏 public summary。

## 总览页信息架构

### 顶部

顶部只保留全局标题、搜索框、简化筛选。原来的状态图例已移除，避免挤占注意力。

### 阅读时间线

阅读时间线是总览页核心模块，包含左侧 calendar/topic 区和右侧 Reading Activity。

展开状态：

- 上方固定主题卡：周一到周日，每天一个固定主题。
- 下方连续日历：一次渲染上月、本月、下月，可在日历区域内上下滚动。
- 右侧 Reading Activity：按实际读后状态发生日期统计，不按 briefing 日期统计。

收起状态：

- 只保留主题卡。
- 今日所在主题卡需要突出，帮助快速看到今天该读什么方向。

### 主题卡

每个主题卡展示：

- 星期与主题名。
- Read Now 完成数，例如 `6/9`。
- Watchlist bonus，例如 `+3`。
- 重要论文累计，例如 `★3`。
- Archive 完成度，例如 `arch 2/5`。
- 当前等级，例如 `Lv.2 推进中`。

主题与星期绑定：

- Mon: RAG
- Tue: Agent / Deep Research
- Wed: Evaluation / Judge
- Thu: Acceleration / Long-Context
- Fri: Learning / Adaptation
- Sat: Findings / Mechanistic
- Sun: Open Rotation

### 日历格

日历格只承担快速状态浏览，不展示论文细节。

保留内容：

- 日期。
- 等级 marker。
- Read Now 完成数。
- Watchlist bonus 数。
- 重要论文星标。
- 底部 Read Now 进度条。

不再展示：

- 状态图例。
- 每篇论文的小色块。
- 主题文字。
- 休/班文字标签。

日期背景含义：

- 普通工作日：白底。
- 周末/节假日：淡绿色。
- 调休工作日：暖黄色。

今日在展开状态下用更强描边和 `TODAY` 标记突出。

### 等级 marker

等级 marker 不依赖字体 glyph，使用 CSS 图形，避免错位。

当前语义：

- Lv.0：未启动，`?`。
- Lv.1：已进入待读/初始推进。
- Lv.2：进行中，圈内半填充。
- Lv.3：Read Now 已处理，但归档链路未齐。
- Lv.4：Read Now 已处理且需要归档的论文均有归档。
- Lv.5：Lv.4 基础上存在 important 论文，是额外信号，不是每天强制目标。

Watchlist 不拖累等级，只作为 bonus。

### Reading Activity

Reading Activity 统计实际读后状态发生日期，而不是 briefing 日期。

作用：

- 某天补读旧 briefing 时，会计入补读当天。
- 点击 activity 日期时，日历中关联的 source briefing 会以虚线联动。
- 右侧列表展示该天处理过的论文和读后状态。

不要把 Reading Activity 改成 briefing 完成度，它的核心价值是“实际阅读贡献”。

## 单篇 briefing 页面

每篇论文的控件保留最小入口。

状态按钮：

- `?`：恢复未选择。
- `不读`：判断不读。
- `待读`：纳入待读。
- `开始读`：复制 Prompt 并跳转到对应 ChatGPT 项目。
- `简单 pass`：读后轻处理。
- `正常读`：正常阅读。
- `重要`：读后高价值。

读后记录只保留两项：

- `ChatGPT share 链接`。
- `你的简短评语`。

已移除：

- GPT 对话链接输入。
- Transcript 大文本框。
- `share 可自动归档`按钮。

旧字段仍保留在 localStorage state 结构中，避免已有记录被破坏；只是 V1 UI 不再把它们作为主要输入。

## 本地状态约定

总览页和 briefing 页都使用浏览器 `localStorage`。

主要 key：

```text
researchBriefings.v2.<paper-id>
researchBriefings.calendarCollapsed
```

paper id 必须稳定。当前 canonical 格式：

```text
<briefing-slug>:read:<index>:<paper-url>
<briefing-slug>:watch:<index>:<paper-url>
```

不要改成 `read-now`、`watchlist` 或带空格的格式，否则旧阅读记录会看起来“消失”。总览页已有 `stateKeyCandidates()` 做兼容迁移，但后续生成器仍应坚持 canonical id。

state 结构保留字段：

```js
{
  decision,
  star,
  conversationUrl,
  shareUrl,
  conversationId,
  projectId,
  transcript,
  userNote,
  readingNote,
  startedAt,
  updatedAt,
  events
}
```

V1 UI 只主动编辑：

- `decision`
- `shareUrl`
- `userNote`
- `startedAt`
- `updatedAt`
- `events`

## 读后状态语义

阅读前/判断：

- `open`：未选择。
- `skip`：不读，是一种完成判断，不需要归档链接。
- `queue`：待读，过程状态。
- `reading`：阅读中，过程状态，允许先贴 share。

读后：

- `pass`：简单 pass。
- `read`：正常读。
- `important`：重要。

读后状态原则上应补 `shareUrl`。UI 会提醒，但不硬阻塞。

## 设计原则

V1 的关键取舍：

1. 总览负责扫状态，不负责判断具体论文。
2. 单篇 briefing 负责读原文和做论文级判断。
3. 论文卡片不要堆太多输入框，读后只记录 share 和个人评语。
4. 主题卡看主题长期状态；日历看 briefing 日期状态；Activity 看真实阅读日期。
5. Watchlist 是 bonus，不纳入主等级硬门槛。
6. 重要论文是额外信号，不要求每天都出现 important。

颜色分层：

- 日期类型一套背景色。
- 主题一套 weekday 色。
- 论文状态色只在按钮、Activity 列表、详情中使用，不塞进月历格。

## 后续生成建议

新增 briefing 后：

1. 先确保 `briefings/<slug>/index.html` 存在。
2. 跑 `python tools\build_dashboard.py` 更新总览数据。
3. 如果新增 briefing 页需要 reader 控件，后续应补一个稳定的 `tools/build_briefing_pages.py` 或把 reader 控件模板抽出，不要继续手工散改 12 个 HTML。
4. 验证 overview JS 与目标 briefing 页 JS。

建议下一步工程化：

- 把总览模板从 `index.html` 抽为 `tools/templates/dashboard.html`。
- 把 briefing reader 控件抽为单一模板/脚本。
- 让 daily automation 发布 briefing 后自动刷新 dashboard。
- 加一个只检查 `localStorage` key 兼容性的测试脚本，避免再次造成“记录消失”的错觉。

更具体的自动化接口、paper id、reader panel、发布后检查项见 `.codex/docs/daily_briefing_dashboard_integration_contract.md`。

## 可借鉴模式

这个 V1 可以迁移到其它学习/阅读追踪场景：

- 固定 weekday topic board：适合周期性主题轮转。
- Calendar + Activity 双时间轴：适合区分“任务来源日期”和“实际完成日期”。
- Level + bonus：适合主任务与额外任务分离。
- Share URL + comment：适合把深度阅读过程外包给 ChatGPT 对话，同时只保留轻量归档。
- CSS marker：适合小尺寸状态图标，避免字体 glyph 错位。

## 下一轮 UI 迭代候选

优先级较高：

- 抽模板，避免手改生成 HTML。
- 给 share URL 做格式化显示和快速打开。
- 在总览页显示“有评语”的论文数量。
- 给 Reading Activity 增加按主题筛选。
- 给单篇 briefing 侧边索引加入阅读状态小标记。

优先级中等：

- 支持导入 ChatGPT share transcript 到本地文件。
- 给每个主题增加长期 important 累计面板。
- 增加月份滚动定位和“回到今天”按钮。

暂不建议：

- 在日历格中恢复每篇论文的小色块。
- 在单篇论文卡片中恢复 transcript 大框。
- 把 Watchlist 纳入主等级硬门槛。
- 用更多图例解释颜色；当前应靠布局和少量文案自解释。

## 已知风险

- 当前总览生成器仍依赖 `index.html` 作为模板，结构可用但工程上不够干净。
- Briefing 页 reader 控件目前是批量替换过的静态 HTML，缺少独立生成器。
- 浏览器 localStorage 是本地状态，换电脑不会自动同步。
- 公开 GitHub Pages 只提供静态页面，无法直接跨域抓取 ChatGPT share transcript。

## V1 完成标准

V1 结束时应满足：

- 总览页能展示主题、日期、实际阅读贡献三层状态。
- 单篇 briefing 能完成论文级判断、读后等级、share 链接和个人评语记录。
- 旧阅读记录不因 paper id 改动而丢失。
- 日历支持连续月份滚动。
- UI 不再展示多余图例、transcript 大框、GPT 对话链接输入。

截至 2026-05-15，本标准已基本满足。

## 2026-05-17 收尾修正

- `开始读` 不再保留单独的 `复制 Prompt` 工具；点击后会把第一轮价值扫描启动词写入剪贴板，并打开统一的 ChatGPT 论文阅读项目。
- Dashboard 的 Reading Week 只显示周一到周六六个 briefing 主题；周日 Open Rotation 不再占用左侧 Week Rail。
- Month Task Map 只表达任务日和 Read Now 完成等级；Reading Activity 表达实际阅读发生日期。
- 已归档论文在 Week Rail 的论文粒度 marker 上显示紫色归档标识。
- `tools/build_dashboard.py` 区分 public/local 状态：
  - `--state-mode public`：不嵌入个人阅读状态，用于 GitHub Pages 发布。
  - `--state-mode local`：从本地 `reading-state.json` 嵌入脱敏状态快照，用于本地或 LAN 页面兜底显示。
- canonical 本地状态优先来自 `E:\Git Repo\Research\.codex\reading_workbench\users\ziang\state\reading-state.json`；旧 OneDrive state 只作为兼容 fallback。
- `assets/local_reading_sync.js` 与 `E:\Git Repo\Research\.codex\tools\local_reading_sync.js` 应保持同源，避免 public 页面和主机工具行为分叉。
