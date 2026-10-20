# pptNprep: ABOT presentation and conference prep

This folder holds slides, notes and Q&A prep for the ABOT paper (IEEE R10-HTC 2026). It is a git
repo shared across machines. Background on the paper, the code and the evidence is in context.md:

@context.md

## Rules for every session

1. **The code directory (`<CODE>`) is read-only.** Never edit, create, delete, move or rename anything inside it. Never run its scripts, tests or training, and never run git commands that change its repo. Read it, and copy files *out* of it into this folder; nothing else.
   - The guard in `.claude/` enforces this. Don't try to work around it, and don't edit `.claude/settings*.json`, `.claude/hooks/` or `.claude/pyguard/` to weaken it.
   - If the user wants the code changed, say it has to be done in a session opened in the code directory itself.
2. **The SessionStart message gives this machine's `<CODE>` path.** If it says the code dir isn't configured, ask the user for the path and have them run `python .claude/hooks/setup_machine.py "<path>"`, then start a new session.
3. **Every number on a slide or in an answer must trace to the camera-ready paper or a committed artifact** (context.md §5). Don't quote earlier drafts, the stale `darwinV2/README.md`, or the pre-audit tables. When the paper and the code disagree (context.md §7), say so rather than smoothing it over.
4. **Keep the paper's framing:** simulation only, the RL part exploratory, link-state routing as the supported result. Don't overclaim.
5. **Put work products** (decks, notes, extracted figures, helper scripts) **in this folder.**
6. **Durable findings go in context.md,** which syncs through git. Machine-local memory doesn't follow you to other machines.
