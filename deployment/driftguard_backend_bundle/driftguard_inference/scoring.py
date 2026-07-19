import json
import math
import re
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

DRIFT_SCORING_SETTINGS = {'class_order': ['benign', 'low', 'medium', 'high', 'critical'], 'severity_anchors': {'benign': 5.0, 'low': 25.0, 'medium': 50.0, 'high': 75.0, 'critical': 95.0}, 'drift_bands': {'stable': {'minimum': 0.0, 'maximum_exclusive': 15.0}, 'watch': {'minimum': 15.0, 'maximum_exclusive': 35.0}, 'concerning': {'minimum': 35.0, 'maximum_exclusive': 60.0}, 'high': {'minimum': 60.0, 'maximum_exclusive': 80.0}, 'critical': {'minimum': 80.0, 'maximum_exclusive': 100.000001}}, 'band_to_label': {'stable': 'benign', 'watch': 'low', 'concerning': 'medium', 'high': 'high', 'critical': 'critical'}, 'score_weights': {'decision_anchor': 0.55, 'expected_probability_risk': 0.45}, 'consensus_bonus': {'two_critical_votes': 8.0, 'two_high_critical_votes': 5.0, 'supported_single_critical_vote': 3.0}, 'operation_bonus': {'security_relevant_removal': 4.0, 'high_risk_addition': 2.0}, 'supported_critical_probability': 0.45, 'commit_score_weights': {'maximum_change_score': 0.5, 'top_three_mean_score': 0.3, 'risk_mass_score': 0.2}, 'file_pressure_half_life_days': 90.0, 'repository_pressure_half_life_days': 45.0, 'event_exposure_weight': 0.65, 'minimum_event_score_for_pressure': 10.0, 'operational_review_queue_size': 1000, 'hotspot_file_count': 100, 'scoring_policy': 'Fixed before final-test evaluation. Validation labels are excluded from scoring inputs.'}

def normalized_entropy(probability_matrix):
    clipped = np.clip(probability_matrix, 1e-12, 1.0)
    entropy = -np.sum(clipped * np.log(clipped), axis=1)
    maximum_entropy = math.log(probability_matrix.shape[1])
    return entropy / maximum_entropy

def assign_drift_band(score):
    score = float(np.clip(score, 0.0, 100.0))
    if score < 15.0:
        return 'stable'
    if score < 35.0:
        return 'watch'
    if score < 60.0:
        return 'concerning'
    if score < 80.0:
        return 'high'
    return 'critical'

def normalized_operation(value):
    if pd.isna(value):
        return ''
    return str(value).strip().lower()

def operation_is_removal(value):
    return normalized_operation(value) in {'delete', 'deleted', 'remove', 'removed'}

def operation_is_addition(value):
    return normalized_operation(value) in {'add', 'added', 'insert', 'inserted', 'create', 'created'}

def build_score_explanation(row):
    explanation_parts = [f"Hybrid decision={row['safety_hybrid_prediction']}", f"model component={row['model_risk_component']:.2f}", f"expected probability risk={row['expected_probability_risk']:.2f}"]
    if float(row['rule_risk_floor']) > 0:
        explanation_parts.append(f"rule floor={row['rule_risk_floor']:.2f}")
    if float(row['consensus_score_bonus']) > 0:
        explanation_parts.append(f"consensus bonus={row['consensus_score_bonus']:.2f}")
    if float(row['operation_score_bonus']) > 0:
        explanation_parts.append(f"operation bonus={row['operation_score_bonus']:.2f}")
    explanation_parts.extend([f"final score={row['change_risk_score']:.2f}", f"confidence={row['score_confidence']:.2f}", f"band={row['drift_band']}"])
    return '; '.join(explanation_parts)

def aggregate_event_scores(score_values):
    values = np.asarray(score_values, dtype=np.float64)
    if len(values) == 0:
        return {'maximum_score': 0.0, 'top_three_mean_score': 0.0, 'risk_mass_score': 0.0, 'event_score': 0.0}
    descending = np.sort(values)[::-1]
    maximum_score = float(descending[0])
    top_three_mean_score = float(descending[:min(3, len(descending))].mean())
    risk_mass = float(np.sum(values / 100.0))
    risk_mass_score = float(100.0 * (1.0 - np.exp(-risk_mass / 4.0)))
    weights = DRIFT_SCORING_SETTINGS['commit_score_weights']
    event_score = weights['maximum_change_score'] * maximum_score + weights['top_three_mean_score'] * top_three_mean_score + weights['risk_mass_score'] * risk_mass_score
    event_score = float(np.clip(event_score, 0.0, 100.0))
    return {'maximum_score': maximum_score, 'top_three_mean_score': top_three_mean_score, 'risk_mass_score': risk_mass_score, 'event_score': event_score}

def calculate_decayed_pressure(dataframe, group_columns, timestamp_column, event_score_column, half_life_days):
    output_records = []
    minimum_event_score = DRIFT_SCORING_SETTINGS['minimum_event_score_for_pressure']
    event_exposure_weight = DRIFT_SCORING_SETTINGS['event_exposure_weight']
    grouped = dataframe.groupby(group_columns, sort=False, dropna=False)
    for group_key, group in grouped:
        group = group.sort_values([timestamp_column, 'commit_hash'])
        previous_pressure = 0.0
        previous_timestamp = None
        for _, row in group.iterrows():
            current_timestamp = row[timestamp_column]
            if previous_timestamp is None:
                elapsed_days = 0.0
            else:
                elapsed_days = max((current_timestamp - previous_timestamp).total_seconds() / 86400.0, 0.0)
            decay_factor = float(0.5 ** (elapsed_days / half_life_days))
            decayed_previous_pressure = previous_pressure * decay_factor
            event_score = float(row[event_score_column])
            normalized_event_exposure = max(event_score - minimum_event_score, 0.0) / (100.0 - minimum_event_score)
            event_exposure = float(np.clip(normalized_event_exposure * event_exposure_weight, 0.0, 1.0))
            current_pressure = 100.0 * (1.0 - (1.0 - decayed_previous_pressure / 100.0) * (1.0 - event_exposure))
            current_pressure = float(np.clip(current_pressure, 0.0, 100.0))
            output_row = row.to_dict()
            output_row.update({'elapsed_days': elapsed_days, 'decay_factor': decay_factor, 'pressure_before_event': decayed_previous_pressure, 'normalized_event_exposure': normalized_event_exposure, 'event_exposure': event_exposure, 'cumulative_drift_pressure': current_pressure, 'cumulative_drift_band': assign_drift_band(current_pressure)})
            output_records.append(output_row)
            previous_pressure = current_pressure
            previous_timestamp = current_timestamp
    return pd.DataFrame(output_records)
