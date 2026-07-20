# AI/ML Module Context — Owner: P1

Read `PROJECT_CONTEXT.md` and `ARCHITECTURE.md` first. This file scopes your specific module.

## Your Mission

Build the Risk Classification Engine and Drift Scoring Engine. You consume Diff Objects (from Backend/P2) and produce Risk Findings and Drift Scores (consumed by Backend/P3 and Frontend/P4). See `RULES.md` for the exact rule set to implement.

## Inputs You Receive

Diff Object (from P2's diff engine — do not wait for real data to start, build against mock diffs first):
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

## Outputs You Must Produce

### Risk Finding (see `RULES.md` for the exact rules that produce risk_tier + rule_triggered)
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
  "rationale": "<filled by LLM call — see below>"
}
```

### Drift Score
```json
{
  "file": "nginx/sites-available/default.conf",
  "baseline_commit": "9f8e7d6",
  "cumulative_score": 34,
  "velocity_flag": true,
  "findings_count": { "critical": 1, "high": 2, "medium": 4, "low": 6 }
}
```

## Build Order (Hours 0–20 of Day 1)

1. **Hours 0–2**: Read `RULES.md`, confirm rule list with team, agree on schemas above.
2. **Hours 2–8**: Build the rule engine as a pure function: `classify(diff_object) -> RiskFinding | None`. Test against hand-written mock diffs covering every rule in `RULES.md` — do NOT wait for P2's real ingestion pipeline.
3. **Hours 8–14**: Once P2 has real structured diffs flowing, wire your rule engine to real data. Validate the rules trigger sensibly (not too noisy, not too sparse) on the real target repo. Start the drift scoring formula (see below).
4. **Hours 14–20**: Finalize drift scoring + velocity flag logic. Package your entire module (`classify()` + `score()`) as a clean importable Python module/function that P2/P3 call directly from the API layer — do not build this as a separate service, it should be a library they import.

## Drift Scoring Formula (design this yourself, but here's a starting point)

Suggested starting formula — adjust based on what looks sensible on your real data:

```
weight = {"Critical": 10, "High": 5, "Medium": 2, "Low": 1}
cumulative_score(file) = sum(weight[finding.risk_tier] for finding in findings_since_baseline(file))
velocity_flag(file) = True if count(findings in last N commits) >= 3 else False
```

Be ready to explain this formula clearly in the Round 1 presentation — it's one of the "Proposed Solution & Innovation" talking points.

## LLM Rationale Integration

You define the rule engine and risk tier; P3 (Backend) owns the actual LLM API call plumbing. Your job: give P3 a clean function signature they can call, e.g.:

```python
def build_rationale_prompt(finding: dict) -> str:
    """Given a Risk Finding (pre-rationale), build the prompt string
    that P3's LLM integration will send to the API."""
    ...
```

Coordinate directly with P3 on this handoff by Hour 8.

## What NOT to Build

- Do not train a custom ML model (no time, no need — CICIDS-style training pipelines are out of scope for this problem). The "ML" in this module is rule-based classification + LLM reasoning, not a trained classifier.
- Do not build the LLM API call plumbing yourself if P3 has already started it — coordinate, don't duplicate.
- Do not attempt the full 4-tier compliance preset system — one hardcoded rule set is enough for Round 1.

## Definition of Done for Round 1

- `classify(diff_object)` returns correct risk tier for all rules in `RULES.md`, tested against both mock and real diffs from the target repo.
- `score(file, findings)` returns a cumulative score and velocity flag.
- Both functions are packaged so P2/P3 can import and call them directly from the API layer.
- 5–10 unit tests exist covering the rule engine (cheap credibility win for "Team Readiness" rubric criterion).
