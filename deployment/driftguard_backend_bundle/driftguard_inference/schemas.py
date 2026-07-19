
from typing import Any

from pydantic import BaseModel, Field


class ConfigurationChange(BaseModel):
    diff_id: str | None = None
    repository: str = "runtime"
    commit_hash: str = "runtime"
    field_path: str = ""
    old_value: Any = ""
    new_value: Any = ""
    configuration_type: str = ""
    parser_mode: str = "structured"
    operation: str = "modified"
    file_path: str = ""
    commit_message: str = ""


class PredictionRequest(BaseModel):
    changes: list[ConfigurationChange] = Field(
        min_length=1
    )


class PredictionResponse(BaseModel):
    results: list[dict]
    commit_summary: dict | None
