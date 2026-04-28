# Research Briefings

Public static site for mobile-readable research briefings.

This repository intentionally contains only published HTML artifacts. The private
source vault, raw notes, prompts, paper queues, and operational logs stay in the
private `Research` repository.

## GitHub Pages Setup

Configure this repository once:

1. Create `yza-thu-eiri/research-briefings` as a public GitHub repository.
2. Push this local repository to GitHub.
3. In GitHub, open `Settings -> Pages`.
4. Set source to `Deploy from a branch`.
5. Select branch `main` and folder `/ (root)`.

Published pages use this URL pattern:

```text
https://yza-thu-eiri.github.io/research-briefings/briefings/<slug>/
```

## Update Flow

The private `Research` repository runs:

```powershell
python .codex\tools\publish_briefing_page.py "Briefings\<briefing>.md"
```

That script renders the briefing HTML into this repository, commits and pushes
this repository, sends the public URL, then commits and pushes only the source
briefing file in the private repository.
