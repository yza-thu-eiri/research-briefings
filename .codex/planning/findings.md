# Findings

## 2026-05-15 Initial Code Review
- Main generator: `tools/build_dashboard.py`.
- Generated files: `index.html` and `briefings/*/index.html`.
- State is stored in `localStorage` under `researchBriefings.v2.<paper.id>`.
- Overview and briefing pages share the same state key, so sync works only within the same browser origin.
- Current code still has a `downloadRecord()` flow in briefing widgets; this should be replaced or hidden if share transcript ingestion is feasible.
- Current `paperStats()` counts all papers together. New design should split `Read Now` from `Watchlist`.
- Existing generated pages should not be edited directly; edit `tools/build_dashboard.py`, then rebuild.

## Open Question: ChatGPT Share Transcript
- Need to verify whether `https://chatgpt.com/share/...` is readable without authentication/network restrictions and whether transcript text is present in server HTML or requires client rendering.

## 2026-05-15 ChatGPT Share Result
- `https://chatgpt.com/share/6a05f340-51fc-83a8-8c3a-412a8918cb56` returns HTTP 200 from local shell.
- The returned HTML contains serialized conversation data including `linear_conversation` and visible content fragments such as the R³AG reading summary.
- This means transcript extraction is feasible from a local/server-side script.
- A purely static GitHub Pages page should not be assumed able to fetch `chatgpt.com` directly because browser CORS may block cross-origin HTML reads.
- UI should store `shareUrl` and allow transcript/note archival; automatic transcript ingestion should be a follow-up local script or automation step unless a backend/proxy is added.

## 2026-05-15 Calendar / Contribution Redesign Check
- The old UI repeats weekday/topic in three places: topic overview cards, calendar weekday header, and daily cells. This causes visual duplication and makes the calendar feel larger than it is.
- Keep the user's liked feature: per-weekday/per-topic aggregate status. Reuse it as the calendar column header instead of rendering a separate weekday header.
- Collapsed state should show only topic aggregate cards plus a single expand control. Expanded state should show the same topic aggregate cards as fixed column headers above the calendar grid.
- Daily calendar cells should not show topic names or topic color dots. Their column already identifies weekday/topic.
- Daily calendar cells should show only task state: date, important count dots, level, Read Now count, progress bar, and Watchlist bonus count.
- Rest days/weekends/holidays should use a positive "good day" palette, not disabled gray. Suggested: soft mint background. Adjusted workdays should use warm amber background/border. Ordinary workdays stay white.
- Important indicator should be purple dots in the top-right corner. Dot count equals important paper count; cap visible dots at 4 and use a plus marker if more.
- Contribution should not repeat briefing completion state. It should only answer actual reading-day questions: how many papers were filed that day, which source briefing dates they came from, and which papers.
- Contribution panel must be height-locked to the calendar area and scroll internally. The whole page should not grow because a contribution day has many papers.

## V1 Closeout Notes
- The first version is considered complete by user judgment on 2026-05-15.
- Current source-of-truth handoff: .codex/docs/research_briefings_dashboard_v1.md.
- Highest-risk next engineering issue is template extraction: overview currently self-templates from index.html, while briefing reader controls are static HTML edits across generated pages.

