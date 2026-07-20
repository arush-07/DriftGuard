# Backend Module Context — Owners: P2 (Ingestion/Diff/DB) + P3 (Auth/API/LLM)

Read `PROJECT_CONTEXT.md` and `ARCHITECTURE.md` first. This file scopes the backend work, split between P2 and P3. Sync every 3–4 hours since you share the DB/API layer.

---

## P2's Scope: Git Ingestion, Diff Engine, DB Layer

### Mission
Pull commit history from the target repo, parse config files structurally (not raw text diff), and produce Diff Objects consumed by P1's risk engine. Own the Postgres schema and data layer.

### Build Order

1. **Hours 0–2**: Confirm target repo + baseline commit with the team (see `PROJECT_CONTEXT.md` Decisions Log). Set up PyDriller against it locally.
2. **Hours 2–8**: Build the PyDriller scan script — walk commit history over the fixed window, extract changed config files. Build the structural parser: load YAML/nginx configs into dicts/trees, diff the trees (not raw text) to produce field-level changes.
3. **Hours 8–14**: Finalize Diff Object output (see schema below), push to Postgres. Start `/findings` and `/diffs` API endpoints (coordinate with P3 who owns the FastAPI app skeleton).
4. **Hours 14–20**: Wire P1's `classify()` and `score()` functions into the pipeline: ingestion → diff → classify → score → store. This is the first full end-to-end run.

### Diff Object Output (must match exactly — consumed by P1)

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

### Parsing Notes
- For YAML/JSON configs: load as nested dict, flatten to dot-notation field paths (e.g., `spec.containers[0].ports[0].containerPort`), diff flattened key sets.
- For nginx configs: use a simple nginx config parser (e.g., `crossplane` Python package, or write a lightweight custom parser for directive blocks) — don't attempt full nginx grammar support, just directive-level key-value extraction.
- Malformed/unparseable files: catch the exception, log it, skip the file — do not crash the pipeline (this is a rubric-relevant reliability point).

### DB Schema (Postgres) — you own this, coordinate with P3 on migrations

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'viewer',
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE findings (
  id SERIAL PRIMARY KEY,
  finding_id TEXT UNIQUE,
  file TEXT NOT NULL,
  commit_hash TEXT,
  timestamp TIMESTAMP,
  risk_tier TEXT,
  confidence FLOAT,
  rule_triggered TEXT,
  field_path TEXT,
  old_value TEXT,
  new_value TEXT,
  rationale TEXT
);

CREATE TABLE drift_scores (
  id SERIAL PRIMARY KEY,
  file TEXT NOT NULL,
  baseline_commit TEXT,
  cumulative_score INT,
  velocity_flag BOOLEAN,
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  action TEXT,
  resource TEXT,
  timestamp TIMESTAMP DEFAULT now()
);
```

---

## P3's Scope: Auth, API Layer, LLM Integration, Report Export

### Mission
Build the FastAPI application shell, JWT auth with 2-role RBAC, the LLM rationale integration, and the report export endpoint. Own the API contract that Frontend (P4) consumes.

### Build Order

1. **Hours 0–2**: Set up FastAPI project skeleton, confirm DB schema with P2, agree on endpoint list (see `ARCHITECTURE.md`).
2. **Hours 2–8**: Build `/auth/signup`, `/auth/login`, `/auth/refresh` — JWT access+refresh tokens, bcrypt password hashing.
3. **Hours 8–14**: Integrate LLM API call for rationale generation (see below). Build role-check middleware (`admin` vs `viewer`).
4. **Hours 14–20**: Wire LLM rationale into the findings pipeline — every Critical/High finding from P1's classifier gets an auto-generated explanation stored via this call. Add RBAC checks to all protected endpoints.
5. **Hours 24–30** (Day 2): Build `/report/export` — generate PDF or markdown summary (exec summary + findings list + remediation checklist template).
6. **Hours 30–34**: Basic audit logging — log `login` and `report_export` events only into `audit_log`.

### LLM Rationale Integration

P1 (ML) provides `build_rationale_prompt(finding: dict) -> str`. Your job: call the LLM API with that prompt and store the result in the finding's `rationale` field.

```python
# Example shape — adapt to whichever LLM API/SDK you're using
def generate_rationale(finding: dict) -> str:
    prompt = build_rationale_prompt(finding)  # from P1's module
    response = call_llm_api(prompt)  # your implementation
    return response.text
```

Keep LLM calls only on Critical/High findings during dev to control cost/rate limits — batch or cache results, don't regenerate on every page load.

### Auth Endpoints — Response Shapes

```
POST /auth/login
Request: {"email": "...", "password": "..."}
Response: {"access_token": "...", "refresh_token": "...", "role": "admin"}
```

### RBAC Rule
- `admin`: all endpoints, including `POST /scan`, `GET /report/export`, `GET /audit-log`
- `viewer`: read-only — `GET /findings`, `GET /drift-scores`, `GET /timeline` only

### Full Endpoint List (you own implementing all of these)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Create user |
| POST | `/auth/login` | No | Returns JWT tokens |
| POST | `/auth/refresh` | Refresh token | New access token |
| GET | `/findings` | Yes | List findings, filterable |
| GET | `/findings/{id}` | Yes | Full finding detail |
| GET | `/drift-scores` | Yes | List drift scores per file |
| GET | `/timeline` | Yes | Chronological events for timeline chart |
| POST | `/scan` | Admin | Trigger fresh ingestion run |
| GET | `/report/export` | Yes | Generate PDF/markdown report |
| GET | `/audit-log` | Admin | List audit events |

### What NOT to Build
- No Redis/Celery queue — endpoints call the pipeline synchronously for Round 1, that's fine for a demo-scale dataset.
- No multi-tenant scoping — single global dataset is fine for Round 1.
- No SSO/OAuth — email+password JWT only.
- No full audit logging of every action — just login + export events.

### Definition of Done for Round 1
- All endpoints in the table above return correct data against real DB records.
- JWT auth works end-to-end: signup → login → authenticated request → refresh.
- Admin vs Viewer permission distinction is visibly enforced (a Viewer token gets 403 on `/scan` and `/report/export`).
- LLM rationale is populated for at least the Critical/High findings shown in the demo.
- Report export produces a real downloadable file with real finding data.
