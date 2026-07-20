# DriftGuard — Architecture

## Full-Vision Pipeline (10-day target, not all built now)

```
Git Webhook/Poller
      │
      ▼
Ingestion Queue (Redis + Celery)          ← ROADMAP, not built in Round 1
      │
      ▼
Structural Diff Engine (PyDriller + parsers)   ← BUILD NOW
      │
      ▼
Risk Classification Engine (Rules + LLM)       ← BUILD NOW
      │
      ▼
Baseline Store (Postgres, versioned)           ← BUILD NOW (simplified)
      │
      ▼
Drift Scoring & Trend Engine                   ← BUILD NOW (simplified formula)
      │
      ▼
Dashboard (RBAC-protected) + Report Generator  ← BUILD NOW (2-role auth only)
      │
      ▼
Notifications (Slack/Email)                    ← ROADMAP, not built in Round 1
```

## Round 1 Simplified Pipeline (what actually runs in 2 days)

```
[Target Git Repo]
      │  PyDriller scan over fixed commit window
      ▼
[Structural Diff Engine]  →  produces Diff Objects
      │
      ▼
[Rule-Based Risk Engine]  →  flags risky diffs
      │
      ▼
[LLM Rationale Call]  →  plain-English explanation for flagged findings
      │
      ▼
[Drift Scoring]  →  cumulative score + velocity flag per file
      │
      ▼
[Postgres: findings, users, audit_log tables]
      │
      ▼
[FastAPI REST API, JWT auth, Admin/Viewer RBAC]
      │
      ▼
[React Dashboard: findings table, timeline, drill-down modal, report export]
```

## Data Contracts (authoritative — do not diverge without team notice)

### 1. Diff Object
Produced by: Backend (P2) — Diff Engine
Consumed by: ML (P1) — Risk Engine

```json
{
  "file": "nginx/sites-available/default.conf",
  "commit_hash": "a1b2c3d",
  "timestamp": "2026-03-14T10:22:00Z",
  "field_path": "server.listen",
  "old_value": "443 ssl",
  "new_value": "80"
}
```

### 2. Risk Finding
Produced by: ML (P1) — Risk Engine + LLM rationale
Consumed by: Backend (P3) — stores in DB, serves via API; Frontend (P4) — displays

```json
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
```

### 3. Drift Score
Produced by: ML (P1) — Scoring Engine
Consumed by: Backend (P3) — stores/serves; Frontend (P4) — displays on timeline

```json
{
  "file": "nginx/sites-available/default.conf",
  "baseline_commit": "9f8e7d6",
  "cumulative_score": 34,
  "velocity_flag": true,
  "findings_count": { "critical": 1, "high": 2, "medium": 4, "low": 6 }
}
```

## API Endpoints (owned by Backend P3, consumed by Frontend P4)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Create user (Admin or Viewer role) |
| POST | `/auth/login` | No | Returns JWT access + refresh token |
| POST | `/auth/refresh` | Refresh token | Returns new access token |
| GET | `/findings` | Yes | List all risk findings, filterable by `?risk_tier=`, `?file=` |
| GET | `/findings/{finding_id}` | Yes | Full detail of one finding incl. diff + rationale |
| GET | `/drift-scores` | Yes | List cumulative drift scores per file |
| GET | `/timeline` | Yes | Chronological event list for timeline chart |
| POST | `/scan` | Yes (Admin only) | Trigger a fresh scan/ingestion run |
| GET | `/report/export` | Yes | Generate and return PDF/markdown report |
| GET | `/audit-log` | Yes (Admin only) | List audit events |

## Auth Model (Round 1 simplified)

- JWT access token (short-lived) + refresh token (longer-lived)
- Two roles only: `admin`, `viewer`
- `admin`: full access, can trigger scans, export reports, view audit log
- `viewer`: read-only access to findings/timeline, cannot trigger scans or export
- Passwords hashed with bcrypt before storage
- Roadmap (not built now): 4-role system (Admin/SecurityReviewer/Developer/Viewer), multi-tenant per-team scoping, SSO/OAuth2

## Database Schema (Postgres, simplified for Round 1)

```sql
users (id, email, password_hash, role, created_at)
findings (id, file, commit_hash, timestamp, risk_tier, confidence, rule_triggered,
          field_path, old_value, new_value, rationale, drift_score_snapshot)
drift_scores (id, file, baseline_commit, cumulative_score, velocity_flag, updated_at)
audit_log (id, user_id, action, resource, timestamp)
```

## Tech Stack

- **Backend**: FastAPI (async), Postgres, SQLAlchemy/asyncpg
- **Auth**: `python-jose` (JWT), `passlib[bcrypt]`
- **Git/Diff**: PyDriller, GitPython, PyYAML (for structural parsing)
- **ML/Risk Engine**: Python rule engine (pure logic, no training needed) + LLM API call (Claude/GPT) for rationale generation
- **Frontend**: React + Vite + Tailwind CSS
- **Report Export**: `reportlab` or `weasyprint` (PDF) or plain markdown-to-PDF via pandoc

## Roadmap Features (NOT built in Round 1 — present as architecture only)

- Redis + Celery async ingestion queue, incremental scanning via webhooks
- Multi-tenant, 4-role RBAC
- Secrets detection (entropy-based scanning for leaked credentials)
- Full audit logging across every action type
- Compliance preset toggles (CIS Benchmark-style rule sets)
- "Explain this drift" live chat (RAG-lite) — Round 1 does one-shot rationale only, not a chat
- Auto-remediation PR generation
- CI/CD webhook triggers, Slack/email notifications
- Docker + Kubernetes deployment
