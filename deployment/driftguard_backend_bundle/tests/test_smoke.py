
from driftguard_inference.engine import (
    DriftGuardEngine,
)


def test_driftguard_smoke():
    engine = DriftGuardEngine(
        device="cpu",
        transformer_batch_size=1,
    )

    response = engine.predict_changes(
        [
            {
                "diff_id": "smoke_001",
                "repository": "smoke-test",
                "commit_hash": "smoke123",
                "field_path": "tls.enabled",
                "old_value": "true",
                "new_value": "false",
                "configuration_type": "yaml",
                "parser_mode": "structured",
                "operation": "modified",
                "file_path": "config.yaml",
                "commit_message": "disable tls",
            }
        ]
    )

    assert len(
        response["results"]
    ) == 1

    result = response[
        "results"
    ][0]

    assert result[
        "safety_hybrid_prediction"
    ] in {
        "benign",
        "low",
        "medium",
        "high",
        "critical",
    }

    assert (
        0.0
        <= result[
            "change_risk_score"
        ]
        <= 100.0
    )

    assert response[
        "commit_summary"
    ] is not None
