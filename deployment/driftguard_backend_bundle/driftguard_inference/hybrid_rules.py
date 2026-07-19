import json
import math
import re
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

HYBRID_ENGINE_SETTINGS = {'class_order': ['benign', 'low', 'medium', 'high', 'critical'], 'risk_rank': {'benign': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}, 'model_weights': {'structured': 0.4, 'transformer': 0.35, 'text_baseline': 0.25}, 'two_model_high_critical_vote_rank': 'high', 'single_critical_support_probability': 0.45, 'low_confidence_threshold': 0.5, 'large_risk_spread_threshold': 2, 'manual_review_queue_size': 750, 'hybrid_score_boost': 0.35, 'production_variant': 'safety_hybrid', 'selection_policy': 'Fixed safety architecture. It is not selected by maximizing weak-label validation performance.'}

CLASS_ORDER = HYBRID_ENGINE_SETTINGS['class_order']

RISK_RANK = HYBRID_ENGINE_SETTINGS['risk_rank']

RANK_TO_CLASS = {rank: class_name for class_name, rank in RISK_RANK.items()}

NULL_LIKE_VALUES = {'', 'none', 'null', 'nil', '~', '<missing>', '<deleted>', 'deleted', 'unset', 'undefined', 'nan'}

FALSE_LIKE_VALUES = {'0', 'false', 'no', 'off', 'disabled', 'disable'}

def normalize_value(value):
    if value is None:
        return ''
    if isinstance(value, float) and np.isnan(value):
        return ''
    return re.sub('\\s+', ' ', str(value).strip().lower())

def contains_pattern(text, pattern):
    return bool(re.search(pattern, text, flags=re.IGNORECASE))

def value_is_missing(value):
    return normalize_value(value) in NULL_LIKE_VALUES

def change_is_removal(operation, new_value):
    normalized_operation = normalize_value(operation)
    return normalized_operation in {'deleted', 'delete', 'removed', 'remove'} or value_is_missing(new_value)

RULE_DEFINITIONS = {'TLS_DISABLED': {'severity': 'critical', 'confidence': 0.99, 'description': 'TLS, SSL, HTTPS, or certificate protection appears to have been disabled or removed.'}, 'AUTH_REMOVED': {'severity': 'critical', 'confidence': 0.99, 'description': 'Authentication, authorization, credentials, or access-control configuration was removed.'}, 'DEFAULT_CREDENTIALS': {'severity': 'critical', 'confidence': 0.99, 'description': 'A credential field appears to use a common default or weak credential.'}, 'OPEN_NETWORK_EXPOSURE': {'severity': 'critical', 'confidence': 0.98, 'description': 'Network access appears open to every address or an unrestricted wildcard.'}, 'PERMISSIVE_ACCESS_CONTROL': {'severity': 'critical', 'confidence': 0.98, 'description': 'An access-control field appears to grant unrestricted or administrative access.'}, 'INSECURE_PROTOCOL': {'severity': 'high', 'confidence': 0.96, 'description': 'An insecure network protocol or obsolete transport-security version was introduced.'}, 'PUBLIC_SERVICE_BINDING': {'severity': 'high', 'confidence': 0.94, 'description': 'A service appears to have been bound publicly or exposed through a wildcard address.'}, 'RESOURCE_LIMIT_REMOVED': {'severity': 'medium', 'confidence': 0.91, 'description': 'A CPU, memory, storage, quota, or timeout limit appears to have been removed.'}}

DEFAULT_CREDENTIAL_VALUES = {'admin', 'administrator', 'root', 'password', 'passwd', 'default', 'changeme', 'change_me', 'changeit', 'secret', 'test', 'demo', 'guest', '1234', '12345', '123456', 'admin123', 'password123'}

GLOBAL_NETWORK_VALUES = {'*', '0.0.0.0', '0.0.0.0/0', '::', '::/0', 'any', 'all', 'world', 'internet'}

PERMISSIVE_ACCESS_VALUES = {'*', 'all', 'any', 'everyone', 'world', 'anonymous', 'public', 'admin', 'administrator', 'cluster-admin', 'root', '777', 'allow all', 'allow_all'}

TLS_FIELD_PATTERN = '(?:tls|ssl|https|certificate|cert|secure_transport|transport_security)'

AUTH_FIELD_PATTERN = '(?:auth|authentication|authorization|password|passwd|secret|token|credential|rbac|access_control|permission|policy)'

CREDENTIAL_FIELD_PATTERN = '(?:password|passwd|secret|token|credential|api_key|apikey|private_key)'

NETWORK_FIELD_PATTERN = '(?:cidr|source_range|allowed_ip|ingress|egress|firewall|security_group|network|subnet|address|listen|bind|host|port)'

ACL_FIELD_PATTERN = '(?:acl|permission|rbac|role|policy|authorization|access_control|allowed_users|allowed_groups|principal)'

RESOURCE_FIELD_PATTERN = '(?:cpu|memory|storage|quota|limit|limits|request|requests|timeout|replica|capacity)'

INSECURE_PROTOCOL_PATTERN = '(?:^|[\\s=:\\"\'])(?:http://|ftp://|telnet://|rsh://|ssl3|sslv3|tls1\\.0|tlsv1\\.0)'

def apply_deterministic_rules_to_row(row):
    field_path = normalize_value(row.get('field_path'))
    old_value = normalize_value(row.get('old_value'))
    new_value = normalize_value(row.get('new_value'))
    operation = normalize_value(row.get('operation'))
    file_path = normalize_value(row.get('file_path'))
    commit_message = normalize_value(row.get('commit_message'))
    matches = []

    def add_match(rule_id, reason):
        definition = RULE_DEFINITIONS[rule_id]
        matches.append({'rule_id': rule_id, 'severity': definition['severity'], 'confidence': definition['confidence'], 'reason': reason})
    removal = change_is_removal(operation=operation, new_value=new_value)
    if contains_pattern(field_path, TLS_FIELD_PATTERN):
        if removal or new_value in FALSE_LIKE_VALUES or new_value in {'disabled', 'insecure', 'plaintext'}:
            add_match('TLS_DISABLED', f"Security field '{field_path}' changed to '{new_value or '<missing>'}'.")
    if removal and contains_pattern(field_path, AUTH_FIELD_PATTERN):
        add_match('AUTH_REMOVED', f"Authentication-related field '{field_path}' was removed.")
    if contains_pattern(field_path, CREDENTIAL_FIELD_PATTERN):
        cleaned_credential = new_value.strip('"\'').strip()
        if cleaned_credential in DEFAULT_CREDENTIAL_VALUES:
            add_match('DEFAULT_CREDENTIALS', f"Credential field '{field_path}' uses common value '{cleaned_credential}'.")
    cleaned_network_value = new_value.strip('"\'').strip()
    if contains_pattern(field_path, NETWORK_FIELD_PATTERN) and cleaned_network_value in GLOBAL_NETWORK_VALUES:
        if contains_pattern(field_path, '(?:cidr|source_range|allowed_ip|ingress|egress|firewall|security_group)'):
            add_match('OPEN_NETWORK_EXPOSURE', f"Network access field '{field_path}' was set to '{cleaned_network_value}'.")
        else:
            add_match('PUBLIC_SERVICE_BINDING', f"Service binding field '{field_path}' was set to '{cleaned_network_value}'.")
    cleaned_access_value = new_value.strip('"\'').strip()
    if contains_pattern(field_path, ACL_FIELD_PATTERN) and cleaned_access_value in PERMISSIVE_ACCESS_VALUES:
        add_match('PERMISSIVE_ACCESS_CONTROL', f"Access-control field '{field_path}' was set to '{cleaned_access_value}'.")
    combined_protocol_text = ' '.join([field_path, new_value, file_path])
    if contains_pattern(combined_protocol_text, INSECURE_PROTOCOL_PATTERN):
        add_match('INSECURE_PROTOCOL', 'An insecure protocol or obsolete transport-security version was detected.')
    if removal and contains_pattern(field_path, RESOURCE_FIELD_PATTERN):
        add_match('RESOURCE_LIMIT_REMOVED', f"Resource-control field '{field_path}' was removed.")
    if not matches:
        return {'rule_match_count': 0, 'matched_rule_ids': '', 'rule_severity': 'benign', 'rule_severity_rank': 0, 'rule_confidence': 0.0, 'rule_reason': ''}
    matches = sorted(matches, key=lambda match: (RISK_RANK[match['severity']], match['confidence']), reverse=True)
    strongest_match = matches[0]
    return {'rule_match_count': len(matches), 'matched_rule_ids': '|'.join((match['rule_id'] for match in matches)), 'rule_severity': strongest_match['severity'], 'rule_severity_rank': RISK_RANK[strongest_match['severity']], 'rule_confidence': float(strongest_match['confidence']), 'rule_reason': ' | '.join((match['reason'] for match in matches))}

def build_hybrid_decision(row):
    ensemble_label = normalize_value(row['weighted_ensemble_prediction'])
    final_rank = RISK_RANK[ensemble_label]
    decision_sources = ['weighted_model_ensemble']
    decision_reasons = [f'Weighted ensemble prediction: {ensemble_label}.']
    if int(row['high_critical_model_votes']) >= 2 and final_rank < RISK_RANK['high']:
        final_rank = RISK_RANK['high']
        decision_sources.append('high_critical_model_consensus')
        decision_reasons.append('At least two learned models predicted high or critical risk.')
    if int(row['critical_model_votes']) >= 2 and final_rank < RISK_RANK['critical']:
        final_rank = RISK_RANK['critical']
        decision_sources.append('critical_model_consensus')
        decision_reasons.append('At least two learned models predicted critical risk.')
    if int(row['critical_model_votes']) >= 1 and float(row['ensemble_high_critical_probability']) >= HYBRID_ENGINE_SETTINGS['single_critical_support_probability'] and (final_rank < RISK_RANK['high']):
        final_rank = RISK_RANK['high']
        decision_sources.append('supported_critical_vote')
        decision_reasons.append('A critical model prediction was supported by the ensemble high/critical probability.')
    pre_rule_rank = final_rank
    rule_rank = int(row['rule_severity_rank'])
    if rule_rank > final_rank:
        final_rank = rule_rank
        decision_sources.append('deterministic_rule_override')
        decision_reasons.append(row['rule_reason'])
    final_label = RANK_TO_CLASS[final_rank]
    rule_override_applied = rule_rank > pre_rule_rank
    return {'safety_hybrid_prediction': final_label, 'safety_hybrid_risk_rank': final_rank, 'decision_source': '|'.join(decision_sources), 'decision_reason': ' '.join((reason for reason in decision_reasons if reason)), 'rule_override_applied': rule_override_applied, 'model_consensus_escalation': any((source in {'high_critical_model_consensus', 'critical_model_consensus', 'supported_critical_vote'} for source in decision_sources))}

def adjust_scores_to_decisions(base_probability_matrix, decision_labels, boost):
    adjusted = np.asarray(base_probability_matrix, dtype=np.float64).copy()
    for row_index, decision_label in enumerate(decision_labels):
        class_index = CLASS_ORDER.index(decision_label)
        adjusted[row_index, class_index] += boost
    adjusted = np.clip(adjusted, 0.0, None)
    adjusted = adjusted / adjusted.sum(axis=1, keepdims=True)
    return adjusted
