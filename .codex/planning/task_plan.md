# Research Briefings Dashboard Iteration Plan

## Goal
把 `research-briefings` 的总览页和单篇 briefing 阅读控件改成适合跨天论文阅读追踪的界面：状态语义清晰、进度有激励感、可挂 GPT 对话/分享链接，并能在总览和单页同步。

## Requested Changes
- [x] 1. `reading` / `queue` 用“虚的色块”表现，不只是边框虚线。
- [x] 2. 验证 ChatGPT share 链接是否可读取 transcript，并据此替代“导出阅读记录”。
- [x] 3. 移除单篇 briefing 里的“导出阅读记录”按钮；若 share 可行，改为 transcript 归档入口。
- [x] 4. 增加“恢复到未选择”状态，默认初始状态显示为 `?`。
- [x] 5. 重新设计 daily level：Read Now 全处理且需链接的都有链接为 Level 4；如果有 important 且有链接为 Level 5。
- [x] 6. Watchlist 不要求每日读完；作为 bonus 点/额外色块，不拖累主等级。
- [x] 7. Level 4/5 的视觉权重加大，尤其紫色等级。
- [x] 8. 总览右下预览的状态统计改为色块表达。
- [x] 9. 日期榜单/等级图标尺寸统一。
- [x] 10. 增加类似 GitHub contribution 的每日色度榜单，并支持一天内多状态拼色。
- [x] 11. 重新评估/简化右上过滤器：全部、未判断、已选择、有对话。
- [x] 12. 右下预览增加 “前沿变化观察” 摘要。
- [x] 13. 粘贴阅读记录后允许用户自己写简短备注。
- [x] 14. `reading` 状态下也允许写入链接地址。
- [x] 15. 重新设计状态色彩，让状态联想清晰、填满感更强。
- [x] 16. 右下预览按钮文案从“进入 briefing 判断”改成更直接的“读原文”。

## Phases
- [x] Phase 1: 读取现有生成脚本，补齐数据提取字段（frontier/change section、read now stats、watchlist bonus）。
- [x] Phase 2: 修改状态模型、颜色、level 规则、总览预览与过滤器。
- [x] Phase 3: 修改单篇 briefing 控件：reset、内联链接/备注、share transcript 入口、移除旧导出。
- [x] Phase 4: 验证 ChatGPT share 链接可访问性；若可读，集成 transcript 抓取策略；若不可读，记录限制并给出替代设计。
- [x] Phase 5: 重建静态页并做语法/本地服务验证。

## Decisions
- 总览等级主要看 `Read Now`，Watchlist 作为 bonus，不拖累日完成。
- `skip` 是已处理状态，不要求链接。
- `pass/read/important` 属于读后状态，需要 GPT 对话或分享链接。
- `queue/reading` 是过程态，不算完成；用虚色块表达。

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| Node syntax-check command failed because PowerShell quoting corrupted inline JS | Tried `node -e` with nested quotes | Switch to here-string piped into `node` |
| `rg` verification command failed because a quoted pattern was not escaped for PowerShell | Tried one long command with embedded HTML quotes | Split verification into simpler literal searches |
| Playwright visual check failed because local browser binaries are missing | Tried Chromium, then Firefox | Kept DOM/build/JS/local-server verification; no browser package install was performed |

## Next Redesign Spec: Topic Header Calendar
- [ ] Replace separate `weekBoard` + `calendar-weekdays` duplication with one reusable topic-header row.
- [ ] Collapsed state: show topic-header row only plus one expand control.
- [ ] Expanded state: topic-header row remains at top of calendar, with month cells directly underneath.
- [ ] Remove weekday/topic text and theme dots from individual day cells.
- [ ] Remove `休` / `班` text labels from day cells; encode day type only by background/border.
- [ ] Change rest-day palette to positive soft mint; adjusted workday to warm amber; ordinary day to white.
- [ ] Replace top-right purple star with important-count dots: 1-4 dots, `+` for overflow.
- [ ] Keep day-cell payload minimal: date, important dots, level mark, Read Now count, Read Now progress bar, Watchlist bonus count.
- [ ] Make `Reading Contribution` same visual height as expanded calendar and scroll internally.
- [ ] Ensure Contribution does not repeat topic aggregate or briefing completion state; it only shows actual reading-day records and source briefing links.
