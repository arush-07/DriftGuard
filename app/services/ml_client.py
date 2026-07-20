import logging
import httpx
from typing import List, Dict, Any
from ..config import settings

logger = logging.getLogger("driftguard.ml_client")

class MLClient:
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
        self.timeout = httpx.Timeout(45.0, read=30.0)

    async def is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"ML service health check failed: {str(e)}")
        return False

    def redact_secrets(self, value: str) -> str:
        if not value:
            return value
        
        # Keywords to trigger redaction
        secret_keywords = ["password", "secret", "token", "api_key", "private_key", "credential"]
        value_lower = str(value).lower()
        
        if any(kw in value_lower for kw in secret_keywords):
            return "[REDACTED]"
        return value

    async def get_predictions(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Perform redaction on values before sending to ML service
        processed_changes = []
        for change in changes:
            processed = change.copy()
            processed["old_value"] = self.redact_secrets(str(change.get("old_value", "")))
            processed["new_value"] = self.redact_secrets(str(change.get("new_value", "")))
            processed_changes.append(processed)

        # Call predict endpoint
        payload = {"changes": processed_changes}
        
        # Verify health first before calling predict
        if not await self.is_healthy():
            logger.error("ML service health check failed before prediction request.")
            raise httpx.HTTPStatusError(
                message="ML Service is unavailable",
                request=None,
                response=httpx.Response(status_code=503)
            )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/predict", json=payload)
            response.raise_for_status()
            return response.json()

ml_client = MLClient()
