# DriftGuard Model Card

## System

DriftGuard detects potentially risky configuration drift in Git-managed
infrastructure and application configuration files.

The exported system combines:

- A character and word TF-IDF linear classifier
- A structured ExtraTrees classifier
- A CodeBERTa-small Transformer classifier
- Eight deterministic security rules
- A safety-oriented hybrid decision engine
- A 0–100 drift scoring and cumulative-pressure engine

## Frozen production configuration

- Primary learned model: `structured`
- Production decision engine: `safety_hybrid`
- Model weights: `{'structured': 0.4, 'transformer': 0.35, 'text_baseline': 0.25}`
- Class order: `['benign', 'low', 'medium', 'high', 'critical']`

## Final test protocol

The final test was repository-disjoint and remained sealed until all model,
rule, hybrid, and drift-scoring settings had been frozen.

Final test repositories:

`['ansible_examples', 'terraform_eks_blueprints']`

Final-test SHA-256:

`cff0f85db740a195366fb81cbad26ba34859f40fe12bf8695b263d1cdedb9b67`

## Final production-hybrid metrics

- Accuracy: 0.423028
- Balanced accuracy: 0.623216
- Macro F1: 0.269263
- Weighted F1: 0.455773
- Macro PR-AUC: 0.463909
- Critical precision: 0.050821
- Critical recall: 0.600000
- High/critical precision: 0.061425
- High/critical recall: 0.600000

## Important limitations

1. Evaluation labels are weak security labels rather than fully independent
   human-verified ground truth.
2. Deterministic-rule metrics partly measure consistency with the weak-label
   rules.
3. Repository and configuration-type distribution shifts can significantly
   reduce generalization.
4. High/critical predictions should be reviewed by a security or platform
   engineer.
5. The cumulative drift-pressure value represents recent risk pressure. It is
   not proof that every previous issue remains active.
6. The system does not execute configuration files or verify whether a
   deployment is currently exploitable.
7. Secrets and configuration values should be handled according to the
   organization's data-retention and access-control requirements.

## Intended use

- Pull-request security screening
- Infrastructure-as-code review
- Configuration-change triage
- Drift hotspot identification
- Commit-level risk prioritization

## Out-of-scope use

- Autonomous blocking without review
- Exploitability confirmation
- Compliance certification
- Replacement for secret scanning, SAST, DAST, policy-as-code, or manual review
