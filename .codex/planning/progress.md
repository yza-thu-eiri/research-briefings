# Progress Log

## 2026-05-15
- Created planning files under `.codex/planning/`.
- Logged all 16 requested UI/behavior changes into `task_plan.md`.
- Confirmed working tree already contains prior dashboard changes and generated static pages.
- Tested ChatGPT share URL access: HTTP 200 and serialized transcript content is present in HTML.
- Decision: implement share URL/transcript fields in static UI; automatic transcript extraction needs local/server-side follow-up because static GitHub Pages likely cannot fetch ChatGPT HTML cross-origin.
- Implemented dashboard/widget changes in `tools/build_dashboard.py`.
- Rebuilt `index.html` and all `briefings/*/index.html`.
- Verified Python compile and JS syntax extraction for overview + one briefing page.
- Removed temporary `tools/__pycache__` and the large share sample HTML from `.codex/planning/`.

- 2026-05-15 follow-up: updated overview interactions for paper search, weekday toggle-only filtering, calendar day filtering, topic color rails, inline status legend, and robust read-original links.

- Rebuilt pages after follow-up; build now includes 12 briefings / 108 papers including 2026-05-15. Verified overview JS syntax and localhost status 200.

- Follow-up: user reported Watchlist bonus is not visually counted after Read Now completion, and mixed top swatches do not distinguish Read Now vs Watchlist.

- Follow-up: split timeline swatches into Read Now and Watchlist bonus lanes; added visible Watchlist bonus dots and +N to level badges.

- Follow-up: remove hover title from split swatches and color Watchlist bonus dots by each paper status.

- Planned accepted: convert week topic cards into category aggregate summaries and replace date strip with compact calendar grid.

- Implemented accepted calendar redesign: topic cards now show aggregate category stats; date strip is now calendar-style cells with Read Now fill, Watchlist dots, and important corner marker.

- Follow-up: redesign date calendar cells as badge system with clean theme rail, level emblem, and Watchlist bonus gems.

- Completed date badge redesign: calendar cells now use a light shell, top topic rail, central Lv.0-Lv.5 emblem, level text, topic label, and bottom Watchlist gems colored by filed status.
- Rebuilt static pages after badge redesign; verified `python -m py_compile`, dashboard build, extracted overview JS syntax, and localhost `http://127.0.0.1:8787/` status 200.
- Visual browser screenshot via Playwright could not run because local Playwright browser binaries are not installed; did not install new browser packages during this pass.

- Follow-up: replaced the tiny date strip with a default-expanded reading calendar panel. Each day now has a larger card with topic rail, date/weekday, topic name, central level emblem, Read Now count/dots, and Watchlist bonus count/dots.
- Added a calendar collapse toggle persisted in `localStorage` under `researchBriefings.calendarCollapsed`.
- Rebuilt pages after large calendar redesign; verified Python compile, dashboard build, overview JS syntax, and localhost status 200.

- Follow-up: converted the reading calendar into a true 7-column month calendar. Empty dates remain visible; weekends, 2026 Labor Day holiday dates, and the 2026-05-09 adjusted workday are marked separately.
- Added `Reading Contribution` as a separate actual-reading graph. It counts filed decision events by actual action date, falls back to `updatedAt` for old states, and links selected contribution days back to source briefing dates via dashed calendar highlights.
- Updated both overview and briefing-page state writers to persist an `events` array for decision/archive events.
- Rebuilt pages after contribution graph work; verified Python compile, dashboard build, overview JS syntax, one generated briefing JS syntax, and localhost status 200.

- Follow-up: reduced calendar color complexity. Calendar cell background now only encodes date type: ordinary day, rest day/weekend/holiday, or adjusted workday. Push topic color is now a small weekday-colored dot, and paper state colors are restricted to compact progress dots/bars.
- Compressed calendar cell height and removed the large central empty mark / large emblem layout for a denser month view.
- Rebuilt pages after color simplification; verified Python compile, dashboard build, overview JS syntax, one generated briefing JS syntax, and localhost status 200.

- Follow-up: moved fixed weekday topics into the weekday header row, further compressed calendar cells to symbol/number-only content, and strengthened ordinary/rest/adjusted-workday contrast.
- Cleaned up a stray zero-byte file named `—` created by a malformed PowerShell verification command.
- Rebuilt pages after compact weekday-topic calendar changes; verified Python compile, dashboard build, overview JS syntax, one generated briefing JS syntax, and localhost status 200.

- Follow-up: corrected calendar compression approach per user feedback. Kept readable text sizes, reduced calendar size by removing low-priority detail rows, hiding per-paper dots in the month grid, placing Reading Contribution beside the calendar, and generating only the weeks needed for the current month instead of a fixed six-row grid.
- Rebuilt pages after side-by-side calendar/contribution layout; verified Python compile, dashboard build, overview JS syntax, one generated briefing JS syntax, and localhost status 200.

- Follow-up: changed collapse behavior to operate on the combined calendar + Reading Contribution block. When collapsed, only the weekday/topic summary board remains plus a thin drawer control; expanding restores both panels side-by-side.
- Adjusted side-by-side layout so calendar and contribution panels stretch to the same height.
- Verified there is only one `calendarToggle` element in generated overview, rebuilt pages, and reran Python/JS/localhost checks successfully.

- Planning checkpoint: user requested a more detailed design pass before more UI edits. Added `Next Redesign Spec: Topic Header Calendar` to `task_plan.md` and logged duplication findings in `findings.md`.

- Implemented topic-header calendar redesign: kept the aggregate weekday/topic board as the only topic overview, removed the duplicate calendar weekday header, and removed topic labels/dots from individual date cells.
- Updated date cells to show only date, level, Read Now count/progress, Watchlist bonus count, and purple important-count dots in the top-right.
- Removed visible `休` / `班` labels from date cells; day type is now communicated by background/border only. Rest days use a softer positive mint palette; adjusted workdays stay warm amber.
- Set calendar and Reading Contribution panels to the same fixed visual height with internal Contribution scrolling.
- Rebuilt pages and verified overview JS syntax plus localhost status 200 after the redesign.

- Follow-up: fixed calendar clipping by turning the calendar panel into a column flex container and making the calendar grid scroll internally.
- Changed important markers from purple dots to top-right purple star icons, still supporting multiple important papers with multiple stars and `+` overflow.

- Implemented unified `阅读时间线` panel: topic aggregate cards, briefing calendar, and actual reading activity now live in one panel instead of separate calendar/contribution cards.
- Replaced right-side `Reading Contribution` card with bottom `Reading Activity` GitHub-style heat strip and selected-day summary; removed explicit heat legend.
- Removed negative margin from the global status legend to prevent overlap with the topic cards.
- Rebuilt generated pages and verified overview JavaScript plus localhost status 200.

- Follow-up: restored side-by-side layout for compact calendar + Reading Activity while keeping both inside the unified timeline panel.
- Added topic-level important accumulation next to main/watch counts in topic headers, formatted as `main · +watch · ★n`.
- Restored a compact daily progress bar in each calendar cell and kept daily important stars in the top-right.
- Rebuilt and verified Python compile/build, overview JS syntax, and localhost status 200.

- Follow-up: removed the top status legend from the overview timeline area, moved the weekday/topic aggregate board into the calendar column so it no longer spans over Reading Activity, changed collapsed behavior to keep the topic board while hiding calendar/activity, tightened the Reading Activity list layout, and aligned daily important stars inside the date row.

- Hotfix: restored canonical paper ids to the prior slug:read:index:url / slug:watch:index:url format so existing localStorage reading records become visible again. Added stateKeyCandidates() to also read and migrate the temporary bad ead-now/watchlist id keys created during the previous generator rewrite. Increased expanded timeline height from 310px to 430px so the calendar shows multiple rows instead of a single clipped row.

- Follow-up: removed the per-paper status color chips from calendar cells. Calendar cells now keep only the bottom Read Now progress bar; status composition remains in Activity/details instead of the dense month grid.

- Follow-up: emphasized today in expanded calendar cells with stronger topic-colored outline and a TODAY marker; emphasized today's weekday/topic card so collapsed mode still surfaces the current theme; increased expanded timeline height to 540px so the calendar exposes roughly one additional week.

- Follow-up: fixed calendar level marker alignment by removing unstable glyph marks from Lv.1-Lv.5 badges and enforcing fixed badge sizing/line-height. Calendar now renders a continuous previous/current/next month range and updates the month label while scrolling, so adjacent months can be reached by vertical scroll instead of only using nav buttons.

- Follow-up: restored the calendar level marker family using CSS-drawn inner shapes instead of text glyphs: Lv2 half-fill, Lv3 solid dot, Lv4/Lv5 diamond. Scroll-linked month labeling now also applies month-visible to the currently visible month so its dates regain normal emphasis while adjacent months remain faded.

- Follow-up: simplified per-paper briefing controls across all 12 generated briefing pages. Post-read record UI now only shows one ChatGPT share URL input and one user comment textarea; removed visible GPT conversation URL input, transcript textarea, and share-hint/archive tool from the paper panels while keeping legacy state fields readable for existing records.

- V1 closeout: created .codex/docs/research_briefings_dashboard_v1.md as the handoff guide for dashboard generation, usage, state conventions, reusable UI patterns, and next UI iteration candidates.

- UI V1 closeout: added .codex/docs/ui_v1_closeout_checklist.md; reran dashboard build, overview JS check, all 12 briefing JS checks, canonical paper-id check, and local HTTP checks for overview + one briefing page. Removed tools/__pycache__.

- Final delivery pass before push: reran python compile, dashboard build, git diff --check, overview inline JS syntax check, all 12 briefing inline JS syntax checks, canonical paper-id check (108/108, no read-now/watchlist bad ids), removed-entry check for conversationUrl / transcript / shareHint, local HTTP checks for overview and 2026-05-12 briefing page, and UTF-8 sanity checks for the V1 docs. All checks passed.

- User raised integration concern before push: daily briefing generation and future agents need an explicit interface contract, not only UI docs. Added `.codex/docs/daily_briefing_dashboard_integration_contract.md`, then updated `research_briefings_dashboard_v1.md` and `ui_v1_closeout_checklist.md` to reference it. The new contract documents private-to-public publish flow, Dashboard parsing requirements, canonical paper ids, localStorage state fields, reader panel requirements, and the V1 engineering gap: new daily briefing pages need a formal reader-control injector or renderer integration.

- Follow-up to integration concern: expanded `.codex/docs/daily_briefing_dashboard_integration_contract.md` with Producer / Consumer boundaries, the exact V1 design facts the daily generator must preserve, a definition of complete daily briefing V1 integration, and fail/skip reporting rules for automation runs.
