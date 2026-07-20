# Frontend + Presentation Module Context — Owner: P4

Read `PROJECT_CONTEXT.md` and `ARCHITECTURE.md` first. You own the dashboard UI, architecture/roadmap diagrams, and the Round 1 slide deck.

## Your Mission

Build the DriftGuard dashboard: login, findings table, timeline chart, drill-down modal, report export button. In parallel, own the visual assets and slide deck for the Round 1 presentation — you are the only role whose output is judged directly by evaluators in a fixed format (slides), so treat the deck as equally important as the UI build.

## Tech Stack

React + Vite + Tailwind CSS. Use `recharts` or `chart.js` for the timeline chart. Keep components simple — this is a 2-day POC, not a polished product; clarity over cleverness.

## Build Order

1. **Hours 0–2**: Set up React+Vite+Tailwind skeleton. Start the architecture diagram (needed for slides regardless of build progress — don't block on backend).
2. **Hours 2–8**: Build static wireframes/mockups first with mock/hardcoded data: login screen, findings table (with severity color-coding), layout shell. No live API calls yet.
3. **Hours 8–14**: Build the findings table component fully (filter by risk tier, sortable), start the login screen UI logic (form + validation, not yet connected).
4. **Hours 14–20**: Connect findings table + timeline chart to real API endpoints as P2/P3 bring them online. Expect breakage — real data reveals edge cases mock data doesn't.
5. **Hours 20–24**: Participate in Day 1 integration checkpoint. Note UI bugs for Day 2.
6. **Hours 24–30** (Day 2): Build the drill-down modal — click a finding, show full diff (old_value → new_value), risk tier, and LLM rationale text.
7. **Hours 30–34**: Polish severity color-coding, filtering, responsive layout. Connect login flow fully to `/auth/login`.
8. **Hours 34–38**: Full-team dry run of the live POC. Immediately after, start building the slide deck using real screenshots from the working app.
9. **Hours 38–42**: Finalize slides, rehearse with the team.

## UI Components Checklist

- [ ] Login screen (email/password, calls `/auth/login`, stores JWT)
- [ ] Findings table: columns = file, risk_tier (color-coded badge), rule_triggered, timestamp; filterable by risk_tier
- [ ] Severity color scheme: Critical = red, High = orange, Medium = yellow, Low = grey/blue
- [ ] Timeline chart: drift events over time (x = date, y = cumulative score or event count), one line/bar per file or aggregated
- [ ] Drill-down modal: triggered by clicking a finding row — shows file, field_path, old_value → new_value, rationale text, risk_tier
- [ ] Report export button: calls `/report/export`, triggers file download
- [ ] Role-aware UI: hide/disable "Trigger Scan" and "Export Report" buttons if logged-in role is `viewer` (not just backend-enforced — show it in the UI too, it's a nice visual RBAC proof point)

## Mock Data (use this shape while backend isn't ready yet — matches real API exactly)

```json
[
  {
    "finding_id": "f-0091",
    "file": "nginx/sites-available/default.conf",
    "commit_hash": "a1b2c3d",
    "timestamp": "2026-03-14T10:22:00Z",
    "risk_tier": "Critical",
    "confidence": 0.92,
    "rule_triggered": "TLS_DISABLED",
    "field_path": "server.listen",
    "old_value": "443 ssl",
    "new_value": "80",
    "rationale": "This change removes TLS termination on the server block, exposing traffic on port 80 without encryption. This is a critical security regression."
  }
]
```

## Architecture & Roadmap Diagram

Build one clear diagram showing the full pipeline (`ARCHITECTURE.md` "Full-Vision Pipeline" section) with a visual distinction (color, dashed border, or a "ROADMAP" label) on the parts NOT built in Round 1 (Redis/Celery queue, 4-role RBAC, secrets detection, CI/CD webhooks, notifications). This single diagram should answer "what did you build vs. what's planned" at a glance — it will likely be your most-scrutinized slide.

## Slide Deck Structure (5–8 slides)

1. Title + Problem Understanding — restate PS-14, why config drift matters to HPE
2. Proposed Solution & Innovation — DriftGuard positioning, hybrid rules+LLM classifier, drift-velocity concept
3. Solution Architecture & Design — the diagram above, built-now vs roadmap clearly marked
4. Technical Feasibility — tech stack + why each choice + how it scales (mention Redis/Celery roadmap here)
5. Initial Progress — real screenshots: findings table, drill-down with rationale, report export; link to GitHub repo
6. Datasets & Scope — target repo chosen, baseline commit, in-scope vs roadmap (Section "Round 1 Scope Boundary" from `PROJECT_CONTEXT.md`)
7. Team Readiness & Execution Plan — task ownership (this file's team table), Day 1/2 plan already executed, 20–30 July roadmap
8. Closing — one-line summary + invite questions

## Definition of Done for Round 1

- Working dashboard connected to real backend data (not just mocks) for at least findings table + drill-down.
- Report export button works end-to-end.
- Role-aware UI visibly differs for admin vs viewer login.
- Architecture diagram clearly separates built vs. roadmap.
- Slide deck complete, using real screenshots, rehearsed as a team.
