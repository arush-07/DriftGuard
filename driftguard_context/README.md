# DriftGuard — Project Context Pack

This folder contains everything needed to hand off DriftGuard (HPE PS-14, Synergy 2026) to a coding agent or a human team and start building immediately.

## How to Use This With an Agent (e.g. Claude Code)

1. Copy this whole folder into your project repo root (or point the agent at it directly).
2. Each person opens a session/agent scoped to their file:
   - **P1 (ML)**: give the agent `PROJECT_CONTEXT.md` + `ARCHITECTURE.md` + `AI_ML_CONTEXT.md` + `RULES.md`
   - **P2 (Backend A)**: give the agent `PROJECT_CONTEXT.md` + `ARCHITECTURE.md` + `BACKEND_CONTEXT.md` (P2 section)
   - **P3 (Backend B)**: give the agent `PROJECT_CONTEXT.md` + `ARCHITECTURE.md` + `BACKEND_CONTEXT.md` (P3 section)
   - **P4 (Frontend)**: give the agent `PROJECT_CONTEXT.md` + `ARCHITECTURE.md` + `FRONTEND_CONTEXT.md`
3. Tell the agent: "Read the attached context files, then start building according to the Build Order section for this role." That's enough to get a working agent session started with full shared context.
4. Everyone should still read `PROJECT_CONTEXT.md` in full at least once — it has the decisions log and scope boundary that affects all modules.

## File Index

| File | Purpose | Primary Owner |
|---|---|---|
| `PROJECT_CONTEXT.md` | Master context: what we're building, team, decisions log, scope boundary | Everyone |
| `ARCHITECTURE.md` | Full system design, data contracts, API spec, DB schema, tech stack | Everyone (reference) |
| `AI_ML_CONTEXT.md` | Risk classification + drift scoring module spec | P1 |
| `RULES.md` | Exact 8 risk-detection rules to implement | P1 |
| `BACKEND_CONTEXT.md` | Git ingestion, diff engine, DB, auth, API, LLM integration, report export | P2 + P3 |
| `FRONTEND_CONTEXT.md` | Dashboard UI spec + slide deck structure | P4 |

## Before Anyone Writes Code (Hour 0 checklist)

- [ ] Fill in the Decisions Log in `PROJECT_CONTEXT.md`: target repo URL, baseline commit, commit window
- [ ] Confirm all 3 data contracts in `ARCHITECTURE.md` are understood by all 4 people
- [ ] Set up shared GitHub repo with branch-per-person structure
- [ ] Each person starts their agent session with their scoped context files above

## Scope Reminder

This is a 2-day Round 1 POC, not the full 10-day build. Every context file has a "What NOT to Build" or "Roadmap Features" section — respect those boundaries so the team ships a working, demoable slice rather than an unfinished full system.
