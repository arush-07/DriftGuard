# DriftGuard — Master Project Context

**Read this file first, regardless of which module you're working on.**

## What This Project Is

DriftGuard is a Configuration Drift Intelligence Platform built for HPE Problem Statement 14 (Synergy 2026 Hackathon, Dept. of CSE, Manipal University Jaipur). It tracks configuration files (YAML, nginx, Terraform, Ansible) across Git history, detects meaningful changes, classifies them by risk level using a hybrid rules + LLM engine, scores cumulative drift against a baseline, and presents findings through an authenticated dashboard with report export.

We are NOT building a script that diffs files. We are building a product: continuous compliance and risk intelligence for infrastructure-as-code, with real auth, RBAC, and a scalable pipeline design — because that framing wins hackathon judging and maps onto real HPE product territory (OpsRamp-style AIOps, GreenLake compliance tooling).

## Current Milestone: Round 1 (2-Day POC)

Round 1 Evaluation is 20th July 2026 (online, 5–8 slide presentation + live POC discussion). We are NOT building the full 10-day vision right now — we are building a focused, working slice that proves the concept end-to-end. See `ARCHITECTURE.md` for the full-vision vs. built-now split.

## Team & File Ownership

| Person | Role | Owns These Context Files |
|---|---|---|
| P1 | ML Engineer | `AI_ML_CONTEXT.md`, `RULES.md` |
| P2 | Backend + AI Engineer A | `BACKEND_CONTEXT.md` (ingestion + diff + DB sections) |
| P3 | Backend + AI Engineer B | `BACKEND_CONTEXT.md` (auth + API + LLM integration sections) |
| P4 | Frontend + Presentation | `FRONTEND_CONTEXT.md` |

Everyone reads `ARCHITECTURE.md` and this file. Nobody starts coding until the shared data contracts (below) are locked.

## Non-Negotiable Data Contracts

These schemas are the interfaces between modules. **Do not change them without notifying every other module owner.** Full detail lives in `ARCHITECTURE.md`, section "Data Contracts" — summarized here:

1. **Diff Object** (produced by Backend/P2, consumed by ML/P1): `{file, commit_hash, timestamp, field_path, old_value, new_value}`
2. **Risk Finding** (produced by ML/P1, consumed by Backend/P3 + Frontend/P4): `{finding_id, file, risk_tier, confidence, rule_triggered, rationale}`
3. **Drift Score** (produced by ML/P1, consumed by Backend/P3 + Frontend/P4): `{file, cumulative_score, velocity_flag, baseline_commit}`
4. **API responses** (produced by Backend/P3, consumed by Frontend/P4): see `BACKEND_CONTEXT.md` for endpoint list and response shapes.

## Target Repo & Dataset

Pick ONE public repo with a long, real config history before coding starts (decide as a team in the first 2 hours):
- Option A: an nginx configuration repo (nginx configs, well-structured, easy to parse)
- Option B: a Kubernetes manifests repo (YAML, more structure/depth to show off)

Whichever is chosen, write the exact repo URL and chosen baseline commit hash into this file's "Decisions Log" section below once fixed.

## Decisions Log (fill in as decided)

- Target repo: `<fill in>`
- Baseline commit: `<fill in>`
- Commit window for demo (e.g. last 50 commits): `<fill in>`

## Round 1 Scope Boundary (what NOT to build yet)

Do not build: Redis/Celery queue, full 4-role RBAC/multi-tenancy, secrets detection, CI/CD webhooks, Slack notifications, compliance preset toggles, auto-remediation PR generation, live chat interface. These are documented as roadmap in the architecture file and presented on a slide — not built in these 2 days. If you find yourself building any of these, stop and re-check scope.

## Success Definition for Round 1

A live (or backup-recorded) walkthrough of: login → dashboard → findings table with real classified data from a real repo → drill-down showing diff + LLM-generated rationale → PDF/markdown report export. Everything else is secondary.
