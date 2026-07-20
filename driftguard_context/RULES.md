# Risk Detection Rules — Owner: P1 (ML)

These are the rule-based detection patterns for the Risk Classification Engine. Implement all of these for Round 1. Each rule maps a diff pattern to a risk tier. Confidence values are starting suggestions — tune based on real data.

## Rule Format

Each rule is a function: `(diff_object) -> {risk_tier, rule_triggered, confidence} | None`

## Round 1 Rule Set (implement all 8)

### 1. TLS_DISABLED — Critical (confidence 0.90+)
Trigger: `field_path` involves `ssl`, `tls`, or `listen` AND `new_value` removes `ssl`/`443`/`tls` that was present in `old_value`.
Example: `listen 443 ssl` → `listen 80`

### 2. AUTH_REMOVED — Critical (confidence 0.90+)
Trigger: `field_path` involves `auth`, `authentication`, `basic_auth`, `require_auth` AND `new_value` disables/removes it (e.g., `enabled: true` → `enabled: false`, or an auth block deleted).

### 3. DEFAULT_CREDENTIALS — Critical (confidence 0.85+)
Trigger: `new_value` contains common default credential patterns: `admin`, `password`, `changeme`, `root:root`, `admin:admin` in a credential-like field (`password`, `secret`, `token`, `credentials`).

### 4. OPEN_PORT_EXPOSURE — High (confidence 0.80+)
Trigger: `field_path` involves `port`, `listen`, `bind` AND `new_value` widens exposure — binds to `0.0.0.0` from a specific IP, or opens a sensitive port (22, 3306, 5432, 6379, 27017, 9200) that wasn't previously exposed.

### 5. PERMISSIVE_ACL — High (confidence 0.75+)
Trigger: `field_path` involves `acl`, `allow`, `access`, `firewall`, `security_group` AND `new_value` is more permissive than `old_value` (e.g., specific CIDR → `0.0.0.0/0`, `deny` → `allow`).

### 6. INSECURE_PROTOCOL — Medium (confidence 0.75+)
Trigger: `new_value` introduces a deprecated/insecure protocol version — `TLSv1.0`, `TLSv1.1`, `SSLv3`, `http` (unencrypted) where `https` was previously specified.

### 7. RESOURCE_LIMIT_REMOVED — Medium (confidence 0.65+)
Trigger: `field_path` involves `limits`, `resources`, `max_connections`, `rate_limit`, `quota` AND the limit is removed entirely or significantly increased/loosened.

### 8. UNCLASSIFIED_SENSITIVE_FIELD_CHANGE — Low (confidence 0.50)
Trigger: fallback rule — `field_path` involves any keyword from a "sensitive fields" list (`security`, `auth`, `access`, `network`, `firewall`, `credential`) but doesn't match rules 1–7. Catches everything else that touches a sensitive area without a specific known pattern, so nothing sensitive is silently ignored.

## Sensitive Field Keywords (used across multiple rules)

```python
SENSITIVE_KEYWORDS = [
    "ssl", "tls", "auth", "password", "secret", "token", "credential",
    "port", "listen", "bind", "acl", "allow", "deny", "access",
    "firewall", "security_group", "limit", "quota", "encryption"
]
```

## Priority / Tie-breaking

If multiple rules match the same diff, use the highest risk tier and report all `rule_triggered` values as a list (or pick the primary one for the schema's single `rule_triggered` field, and mention the rest in the rationale).

## Testing Checklist

Write at least one test diff per rule to confirm detection works before wiring to real data:
- [ ] TLS_DISABLED
- [ ] AUTH_REMOVED
- [ ] DEFAULT_CREDENTIALS
- [ ] OPEN_PORT_EXPOSURE
- [ ] PERMISSIVE_ACL
- [ ] INSECURE_PROTOCOL
- [ ] RESOURCE_LIMIT_REMOVED
- [ ] UNCLASSIFIED_SENSITIVE_FIELD_CHANGE (fallback)
- [ ] A diff that should NOT trigger any rule (true negative — a harmless config change)

## Roadmap Rules (not built now — mention on the architecture slide)

- Compliance-preset-driven rules (CIS Benchmark, NIST, PCI-DSS specific rule sets, toggleable per team)
- Secrets/entropy-based detection for leaked API keys or tokens not caught by keyword matching
- Cross-file correlation rules (e.g., a change in one file that combined with another file's state creates risk)
