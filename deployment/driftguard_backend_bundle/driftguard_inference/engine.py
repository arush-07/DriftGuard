
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

from . import baseline_features
from . import structured_features
from . import transformer_features
from . import hybrid_rules
from . import scoring


BUNDLE_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = BUNDLE_ROOT / "models"
CONFIGS_DIR = BUNDLE_ROOT / "configs"

CLASS_ORDER = ['benign', 'low', 'medium', 'high', 'critical']
RISK_RANK = {'benign': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
RANK_TO_CLASS = {
    rank: label
    for label, rank
    in RISK_RANK.items()
}

MODEL_WEIGHTS = {'structured': 0.4, 'transformer': 0.35, 'text_baseline': 0.25}
BASELINE_TEXT_BUILDER_NAME = 'build_baseline_text'
TRANSFORMER_TEXT_BUILDER_NAME = 'build_transformer_text'

BASELINE_TEXT_BUILDER = getattr(
    baseline_features,
    BASELINE_TEXT_BUILDER_NAME,
)

TRANSFORMER_TEXT_BUILDER = getattr(
    transformer_features,
    TRANSFORMER_TEXT_BUILDER_NAME,
)


def _load_json(path):
    with Path(path).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


HYBRID_SETTINGS = _load_json(
    CONFIGS_DIR
    / "hybrid_engine_settings.json"
)

SCORING_SETTINGS = _load_json(
    CONFIGS_DIR
    / "drift_scoring_settings.json"
)

STRUCTURED_SETTINGS = _load_json(
    CONFIGS_DIR
    / "structured_model_training_settings.json"
)

structured_features.STRUCTURED_SETTINGS = (
    STRUCTURED_SETTINGS
)

hybrid_rules.HYBRID_ENGINE_SETTINGS = (
    HYBRID_SETTINGS
)

hybrid_rules.CLASS_ORDER = CLASS_ORDER
hybrid_rules.RISK_RANK = RISK_RANK
hybrid_rules.RANK_TO_CLASS = RANK_TO_CLASS
hybrid_rules.MODEL_WEIGHTS = MODEL_WEIGHTS

scoring.DRIFT_SCORING_SETTINGS = (
    SCORING_SETTINGS
)

scoring.CLASS_ORDER = CLASS_ORDER
scoring.SEVERITY_ANCHORS = (
    SCORING_SETTINGS[
        "severity_anchors"
    ]
)

scoring.BAND_TO_LABEL = (
    SCORING_SETTINGS[
        "band_to_label"
    ]
)


def _unwrap_model(saved_object):
    if not isinstance(
        saved_object,
        dict,
    ):
        return saved_object

    for key in [
        "model",
        "pipeline",
        "best_model",
        "classifier",
        "estimator",
    ]:
        if key in saved_object:
            return saved_object[key]

    raise ValueError(
        "No model object was found in the "
        "saved artifact."
    )


def _classifier_classes(model):
    if hasattr(
        model,
        "classes_",
    ):
        return np.asarray(
            model.classes_
        ).astype(str)

    if hasattr(
        model,
        "named_steps",
    ):
        for step in reversed(
            list(
                model.named_steps.values()
            )
        ):
            if hasattr(
                step,
                "classes_",
            ):
                return np.asarray(
                    step.classes_
                ).astype(str)

    raise AttributeError(
        "Classifier classes were not found."
    )


def _softmax(values):
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    shifted = (
        values
        - values.max(
            axis=1,
            keepdims=True,
        )
    )

    exponentials = np.exp(
        shifted
    )

    return (
        exponentials
        / exponentials.sum(
            axis=1,
            keepdims=True,
        )
    )


def _align_matrix(
    matrix,
    source_classes,
):
    matrix = np.asarray(
        matrix,
        dtype=np.float64,
    )

    aligned = np.zeros(
        (
            matrix.shape[0],
            len(CLASS_ORDER),
        ),
        dtype=np.float64,
    )

    source_classes = [
        str(value).strip().lower()
        for value in source_classes
    ]

    for source_index, class_name in enumerate(
        source_classes
    ):
        if class_name not in CLASS_ORDER:
            continue

        aligned[
            :,
            CLASS_ORDER.index(
                class_name
            ),
        ] = matrix[
            :,
            source_index,
        ]

    return aligned


def _normalize_probabilities(matrix):
    matrix = np.asarray(
        matrix,
        dtype=np.float64,
    )

    matrix = np.clip(
        matrix,
        0.0,
        None,
    )

    zero_rows = (
        matrix.sum(
            axis=1
        )
        <= 0
    )

    if zero_rows.any():
        matrix[
            zero_rows
        ] = (
            1.0
            / len(CLASS_ORDER)
        )

    return (
        matrix
        / matrix.sum(
            axis=1,
            keepdims=True,
        )
    )


class DriftGuardEngine:
    def __init__(
        self,
        device=None,
        transformer_batch_size=8,
    ):
        self.device = torch.device(
            device
            if device is not None
            else (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
        )

        self.transformer_batch_size = (
            transformer_batch_size
        )

        self.text_model = _unwrap_model(
            joblib.load(
                MODELS_DIR
                / "text_baseline_model.joblib"
            )
        )

        self.structured_model = _unwrap_model(
            joblib.load(
                MODELS_DIR
                / "structured_model.joblib"
            )
        )

        transformer_path = (
            MODELS_DIR
            / "transformer_model"
        )

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                transformer_path
            )
        )

        self.transformer_model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                transformer_path
            )
            .to(
                self.device
            )
        )

        self.transformer_model.eval()

    @staticmethod
    def _prepare_dataframe(
        changes,
    ):
        dataframe = pd.DataFrame(
            changes
        ).copy()

        required_columns = [
            "field_path",
            "old_value",
            "new_value",
            "configuration_type",
            "parser_mode",
            "operation",
            "file_path",
            "commit_message",
        ]

        for column in required_columns:
            if column not in dataframe.columns:
                dataframe[column] = ""

        if "repository" not in dataframe.columns:
            dataframe["repository"] = "runtime"

        if "commit_hash" not in dataframe.columns:
            dataframe["commit_hash"] = "runtime"

        if "diff_id" not in dataframe.columns:
            dataframe["diff_id"] = [
                f"runtime_{index}"
                for index in range(
                    len(dataframe)
                )
            ]

        return dataframe.reset_index(
            drop=True
        )

    def _run_text_model(
        self,
        dataframe,
    ):
        documents = pd.Series(
            BASELINE_TEXT_BUILDER(
                dataframe.copy()
            )
        ).fillna("").astype(str)

        predictions = self.text_model.predict(
            documents
        )

        classes = _classifier_classes(
            self.text_model
        )

        if hasattr(
            self.text_model,
            "decision_function",
        ):
            raw_scores = (
                self.text_model
                .decision_function(
                    documents
                )
            )

            aligned_scores = _align_matrix(
                raw_scores,
                classes,
            )

            probabilities = _softmax(
                aligned_scores
            )

        else:
            raw_probabilities = (
                self.text_model.predict_proba(
                    documents
                )
            )

            probabilities = _align_matrix(
                raw_probabilities,
                classes,
            )

        return (
            np.asarray(
                predictions
            ).astype(str),

            _normalize_probabilities(
                probabilities
            ),
        )

    def _run_structured_model(
        self,
        dataframe,
    ):
        features = (
            structured_features
            .engineer_structured_features(
                dataframe.copy()
            )
        )

        predictions = (
            self.structured_model.predict(
                features
            )
        )

        classes = _classifier_classes(
            self.structured_model
        )

        if hasattr(
            self.structured_model,
            "predict_proba",
        ):
            raw_probabilities = (
                self.structured_model
                .predict_proba(
                    features
                )
            )

            probabilities = _align_matrix(
                raw_probabilities,
                classes,
            )

        else:
            raw_scores = (
                self.structured_model
                .decision_function(
                    features
                )
            )

            probabilities = _softmax(
                _align_matrix(
                    raw_scores,
                    classes,
                )
            )

        return (
            np.asarray(
                predictions
            ).astype(str),

            _normalize_probabilities(
                probabilities
            ),
        )

    def _run_transformer(
        self,
        dataframe,
    ):
        documents = pd.Series(
            TRANSFORMER_TEXT_BUILDER(
                dataframe.copy()
            )
        ).fillna("").astype(str).tolist()

        batches = []

        for start in range(
            0,
            len(documents),
            self.transformer_batch_size,
        ):
            encoded = self.tokenizer(
                documents[
                    start:
                    start
                    + self.transformer_batch_size
                ],
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )

            encoded = {
                key: value.to(
                    self.device
                )
                for key, value
                in encoded.items()
            }

            with torch.no_grad():
                output = self.transformer_model(
                    **encoded
                )

                probabilities = (
                    torch.softmax(
                        output.logits.float(),
                        dim=1,
                    )
                    .cpu()
                    .numpy()
                )

            batches.append(
                probabilities
            )

        probabilities = (
            _normalize_probabilities(
                np.vstack(
                    batches
                )
            )
        )

        predicted_ids = probabilities.argmax(
            axis=1
        )

        predictions = np.array(
            [
                CLASS_ORDER[
                    class_index
                ]
                for class_index
                in predicted_ids
            ]
        )

        return (
            predictions,
            probabilities,
        )

    def predict_changes(
        self,
        changes,
    ):
        dataframe = self._prepare_dataframe(
            changes
        )

        if dataframe.empty:
            return {
                "results": [],
                "commit_summary": None,
            }

        model_outputs = {}

        (
            model_outputs[
                "text_baseline"
            ],
            text_probabilities,
        ) = self._run_text_model(
            dataframe
        )

        (
            model_outputs[
                "structured"
            ],
            structured_probabilities,
        ) = self._run_structured_model(
            dataframe
        )

        (
            model_outputs[
                "transformer"
            ],
            transformer_probabilities,
        ) = self._run_transformer(
            dataframe
        )

        probabilities_by_model = {
            "structured":
                structured_probabilities,

            "transformer":
                transformer_probabilities,

            "text_baseline":
                text_probabilities,
        }

        result = dataframe.copy()

        for model_name in [
            "structured",
            "transformer",
            "text_baseline",
        ]:
            result[
                f"{model_name}_prediction"
            ] = model_outputs[
                model_name
            ]

            result[
                f"{model_name}_confidence"
            ] = probabilities_by_model[
                model_name
            ].max(
                axis=1
            )

            for class_index, class_name in enumerate(
                CLASS_ORDER
            ):
                result[
                    f"{model_name}_score_{class_name}"
                ] = probabilities_by_model[
                    model_name
                ][
                    :,
                    class_index,
                ]

        rule_results = result.apply(
            hybrid_rules
            .apply_deterministic_rules_to_row,
            axis=1,
            result_type="expand",
        ).rename(
            columns={
                "matched_rule_ids":
                    "deterministic_rule_ids",
            }
        )

        result = pd.concat(
            [
                result.reset_index(
                    drop=True
                ),
                rule_results.reset_index(
                    drop=True
                ),
            ],
            axis=1,
        )

        ensemble = np.zeros(
            (
                len(result),
                len(CLASS_ORDER),
            ),
            dtype=np.float64,
        )

        for model_name, model_weight in (
            MODEL_WEIGHTS.items()
        ):
            ensemble += (
                float(
                    model_weight
                )
                * probabilities_by_model[
                    model_name
                ]
            )

        ensemble = _normalize_probabilities(
            ensemble
        )

        ensemble_ids = ensemble.argmax(
            axis=1
        )

        result[
            "weighted_ensemble_prediction"
        ] = [
            CLASS_ORDER[
                class_index
            ]
            for class_index
            in ensemble_ids
        ]

        result[
            "weighted_ensemble_confidence"
        ] = ensemble.max(
            axis=1
        )

        for class_index, class_name in enumerate(
            CLASS_ORDER
        ):
            result[
                f"weighted_ensemble_score_{class_name}"
            ] = ensemble[
                :,
                class_index,
            ]

        prediction_columns = [
            "structured_prediction",
            "transformer_prediction",
            "text_baseline_prediction",
        ]

        prediction_frame = (
            result[
                prediction_columns
            ]
            .fillna("benign")
            .astype(str)
            .apply(
                lambda column:
                column.str.strip().str.lower()
            )
        )

        rank_frame = prediction_frame.replace(
            RISK_RANK
        )

        result[
            "model_unique_prediction_count"
        ] = prediction_frame.nunique(
            axis=1
        )

        result[
            "model_three_way_disagreement"
        ] = (
            result[
                "model_unique_prediction_count"
            ]
            == 3
        )

        result[
            "model_minimum_risk_rank"
        ] = rank_frame.min(
            axis=1
        )

        result[
            "model_maximum_risk_rank"
        ] = rank_frame.max(
            axis=1
        )

        result[
            "model_risk_spread"
        ] = (
            result[
                "model_maximum_risk_rank"
            ]
            - result[
                "model_minimum_risk_rank"
            ]
        )

        result[
            "high_critical_model_votes"
        ] = prediction_frame.isin(
            [
                "high",
                "critical",
            ]
        ).sum(
            axis=1
        )

        result[
            "critical_model_votes"
        ] = prediction_frame.eq(
            "critical"
        ).sum(
            axis=1
        )

        result[
            "ensemble_high_critical_probability"
        ] = (
            result[
                "weighted_ensemble_score_high"
            ]
            + result[
                "weighted_ensemble_score_critical"
            ]
        )

        hybrid_decisions = result.apply(
            hybrid_rules
            .build_hybrid_decision,
            axis=1,
            result_type="expand",
        )

        result = pd.concat(
            [
                result,
                hybrid_decisions,
            ],
            axis=1,
        )

        hybrid_probabilities = (
            hybrid_rules
            .adjust_scores_to_decisions(
                ensemble,

                result[
                    "safety_hybrid_prediction"
                ].tolist(),

                boost=(
                    HYBRID_SETTINGS[
                        "hybrid_score_boost"
                    ]
                ),
            )
        )

        hybrid_probabilities = (
            _normalize_probabilities(
                hybrid_probabilities
            )
        )

        result[
            "safety_hybrid_confidence"
        ] = hybrid_probabilities.max(
            axis=1
        )

        for class_index, class_name in enumerate(
            CLASS_ORDER
        ):
            result[
                f"safety_hybrid_score_{class_name}"
            ] = hybrid_probabilities[
                :,
                class_index,
            ]

        severity_anchor_vector = np.array(
            [
                SCORING_SETTINGS[
                    "severity_anchors"
                ][
                    class_name
                ]
                for class_name in CLASS_ORDER
            ],
            dtype=np.float64,
        )

        expected_risk = (
            hybrid_probabilities
            @ severity_anchor_vector
        )

        decision_anchor = (
            result[
                "safety_hybrid_prediction"
            ]
            .map(
                SCORING_SETTINGS[
                    "severity_anchors"
                ]
            )
            .to_numpy(
                dtype=np.float64
            )
        )

        model_component = (
            SCORING_SETTINGS[
                "score_weights"
            ][
                "decision_anchor"
            ]
            * decision_anchor

            + SCORING_SETTINGS[
                "score_weights"
            ][
                "expected_probability_risk"
            ]
            * expected_risk
        )

        rule_anchor = (
            result[
                "rule_severity"
            ]
            .map(
                SCORING_SETTINGS[
                    "severity_anchors"
                ]
            )
            .fillna(0.0)
            .to_numpy(
                dtype=np.float64
            )
        )

        rule_confidence = (
            result[
                "rule_confidence"
            ]
            .fillna(0.0)
            .clip(
                lower=0.0,
                upper=1.0,
            )
            .to_numpy(
                dtype=np.float64
            )
        )

        rule_floor = np.where(
            result[
                "rule_match_count"
            ].fillna(0).gt(0),

            rule_anchor
            * (
                0.65
                + 0.35
                * rule_confidence
            ),

            0.0,
        )

        critical_votes = result[
            "critical_model_votes"
        ].to_numpy(
            dtype=np.float64
        )

        high_critical_votes = result[
            "high_critical_model_votes"
        ].to_numpy(
            dtype=np.float64
        )

        supported_probability = result[
            "ensemble_high_critical_probability"
        ].to_numpy(
            dtype=np.float64
        )

        consensus_bonus = np.select(
            [
                critical_votes >= 2,

                high_critical_votes >= 2,

                (
                    critical_votes >= 1
                )
                & (
                    supported_probability
                    >= SCORING_SETTINGS[
                        "supported_critical_probability"
                    ]
                ),
            ],
            [
                SCORING_SETTINGS[
                    "consensus_bonus"
                ][
                    "two_critical_votes"
                ],

                SCORING_SETTINGS[
                    "consensus_bonus"
                ][
                    "two_high_critical_votes"
                ],

                SCORING_SETTINGS[
                    "consensus_bonus"
                ][
                    "supported_single_critical_vote"
                ],
            ],
            default=0.0,
        )

        change_scores = np.clip(
            np.maximum(
                model_component,
                rule_floor,
            )
            + consensus_bonus,
            0.0,
            100.0,
        )

        entropy = scoring.normalized_entropy(
            hybrid_probabilities
        )

        result[
            "expected_probability_risk"
        ] = expected_risk

        result[
            "model_risk_component"
        ] = model_component

        result[
            "rule_risk_floor"
        ] = rule_floor

        result[
            "consensus_score_bonus"
        ] = consensus_bonus

        result[
            "change_risk_score"
        ] = change_scores

        result[
            "uncertainty_score"
        ] = entropy * 100.0

        result[
            "drift_band"
        ] = result[
            "change_risk_score"
        ].apply(
            scoring.assign_drift_band
        )

        output_columns = [
            "diff_id",
            "repository",
            "commit_hash",
            "file_path",
            "field_path",
            "old_value",
            "new_value",
            "operation",
            "configuration_type",
            "safety_hybrid_prediction",
            "safety_hybrid_confidence",
            "change_risk_score",
            "uncertainty_score",
            "drift_band",
            "deterministic_rule_ids",
            "decision_source",
            "decision_reason",
        ]

        commit_aggregate = (
            scoring.aggregate_event_scores(
                result[
                    "change_risk_score"
                ].to_numpy()
            )
        )

        commit_summary = {
            "changed_fields":
                int(
                    len(result)
                ),

            "changed_files":
                int(
                    result[
                        "file_path"
                    ].nunique()
                ),

            "maximum_change_score":
                commit_aggregate[
                    "maximum_score"
                ],

            "top_three_mean_score":
                commit_aggregate[
                    "top_three_mean_score"
                ],

            "risk_mass_score":
                commit_aggregate[
                    "risk_mass_score"
                ],

            "commit_drift_score":
                commit_aggregate[
                    "event_score"
                ],

            "commit_drift_band":
                scoring.assign_drift_band(
                    commit_aggregate[
                        "event_score"
                    ]
                ),
        }

        records = json.loads(
            result[
                output_columns
            ].to_json(
                orient="records"
            )
        )

        return {
            "results": records,
            "commit_summary": commit_summary,
        }
