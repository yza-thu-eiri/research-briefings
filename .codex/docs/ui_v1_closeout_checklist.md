# UI V1 Closeout Checklist

## 当前结论

Research Briefings Dashboard V1 的 UI 设计阶段已进入收尾状态。当前版本的核心结构可以冻结：总览页负责状态扫描，单篇 briefing 页负责论文级判断和轻量归档。

## 冻结范围

- 总览页顶部：标题、搜索、简化筛选。
- 主题总览：按周一到周日固定主题组织。
- 阅读日历：连续月份滚动、今日突出、日期类型背景、等级 marker、Read Now 进度条。
- Reading Activity：按实际阅读发生日期统计。
- 单篇论文控件：状态按钮、ChatGPT share 链接、个人评语、复制 Prompt。

## 不再回退的设计决定

- 不恢复顶部状态图例。
- 不在日历格中展示每篇论文的小色块。
- 不在论文卡片中展示 GPT 对话链接输入。
- 不在论文卡片中展示 transcript 大文本框。
- 不把 Watchlist 纳入主等级硬门槛。
- 不要求每天都有 important 论文。

## 发布前检查

- `tools/build_dashboard.py` 能编译。
- `python tools\build_dashboard.py` 能重建总览数据。
- `index.html` 内联脚本语法通过。
- 所有 `briefings/*/index.html` 内联脚本语法通过。
- 首页和至少一个 briefing 页本地 HTTP 返回 `200`。
- 单篇 briefing 页不再包含可见的 `conversationUrl` 或 `transcript` 输入字段。
- Paper id 仍使用 canonical 格式：`slug:read:index:url` / `slug:watch:index:url`。
- 每日 briefing 生成/发布接口已记录在 `.codex/docs/daily_briefing_dashboard_integration_contract.md`。
- 新增 briefing 只有在 Dashboard 已刷新且新页面具备 reader 控件时，才算完整接入 V1。

## 下一阶段第一优先级

工程化模板抽取，而不是继续调 UI。

建议拆成两个后续任务：

1. 把 `index.html` 自模板模式改成 `tools/templates/dashboard.html`。
2. 把 briefing reader 控件抽成统一模板或生成器，避免继续批量替换静态 HTML。
3. 将 `.codex/docs/daily_briefing_dashboard_integration_contract.md` 中的 reader 注入方案落地到发布链路。

## 接手提示

如果后续发现“阅读记录消失”，优先检查 paper id 是否变化，不要先清空 localStorage。总览页已有 `stateKeyCandidates()` 做兼容迁移，但生成器仍应坚持 canonical id。
