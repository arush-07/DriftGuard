from unittest.mock import AsyncMock, patch
import pytest

from app.auth import get_password_hash
from app import models

@pytest.fixture(scope="function")
def admin_user(db):
    user = models.User(
        email="testadmin@driftguard.io",
        full_name="Test Admin",
        password_hash=get_password_hash("admin123"),
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers(client, admin_user):
    login_payload = {
        "email": "testadmin@driftguard.io",
        "password": "admin123"
    }
    response = client.post("/auth/login", json=login_payload)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_and_list_repositories(client, auth_headers):
    # Create
    repo_payload = {
        "name": "Synergy-2026/k8s-nginx-config-repo",
        "provider": "github",
        "clone_url": "https://github.com/Synergy-2026/k8s-nginx-config-repo.git",
        "default_branch": "main"
    }
    response = client.post("/api/v1/repositories", json=repo_payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Synergy-2026/k8s-nginx-config-repo"
    repo_id = response.json()["id"]

    # List
    response = client.get("/api/v1/repositories", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["id"] == repo_id

@patch("app.routers.scans.ml_client.is_healthy", new_callable=AsyncMock)
@patch("app.routers.scans.ml_client.get_predictions", new_callable=AsyncMock)
def test_trigger_scan_success(mock_predict, mock_healthy, client, db, auth_headers):
    # Mock ML client
    mock_healthy.return_value = True
    mock_predict.return_value = {
        "results": [
            {
                "diff_id": "test-diff-id",
                "field_path": "server.listen",
                "file_path": "nginx.conf",
                "drift_band": "high",
                "safety_hybrid_prediction": "unsafe",
                "safety_hybrid_confidence": 0.88,
                "change_risk_score": 75.0,
                "deterministic_rule_ids": ["TLS_DISABLED"],
                "model_version": "v1.0.0-ml",
                "decision_reason": "TLS listen configuration regression"
            }
        ]
    }

    # Setup repo
    repo = models.Repository(
        name="test-repo",
        provider="manual"
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    scan_payload = {
        "repository_id": repo.id,
        "commit_sha": "abc1234",
        "changes": [
            {
                "file_path": "nginx.conf",
                "configuration_type": "nginx",
                "field_path": "server.listen",
                "old_value": "443 ssl",
                "new_value": "80",
                "commit_message": "disable tls",
                "commit_hash": "abc1234"
            }
        ]
    }

    # Trigger scan
    response = client.post("/api/v1/scans", json=scan_payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["status"] == "queued"
