import json
import math
import re
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

STRUCTURED_SETTINGS = {'random_seed': 42, 'class_order': ['benign', 'low', 'medium', 'high', 'critical'], 'one_hot_minimum_frequency': 5, 'one_hot_maximum_categories': 100, 'maximum_value_processing_length': 4000, 'maximum_path_processing_length': 2000, 'maximum_commit_message_length': 2000, 'permutation_importance_repeats': 5, 'permutation_importance_top_n': 30, 'minimum_configuration_group_size': 10, 'selection_metrics': ['macro_f1', 'critical_recall', 'high_critical_recall', 'balanced_accuracy']}

def normalize_text_series(series, maximum_length):
    normalized = series.fillna('').astype(str).str.replace('\r', ' ', regex=False).str.replace('\n', ' ', regex=False).str.replace('\t', ' ', regex=False).str.replace('\\s+', ' ', regex=True).str.strip()
    return normalized.str.slice(0, maximum_length)

def character_entropy(value):
    text = str(value)
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    entropy = 0.0
    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
    return float(entropy)

def infer_value_type(value):
    if value is None:
        return 'missing'
    text = str(value).strip()
    if not text:
        return 'empty'
    lowered = text.lower()
    if lowered in {'null', 'none', 'nil', '~', '<missing>'}:
        return 'null_like'
    if lowered in {'true', 'false', 'yes', 'no', 'on', 'off'}:
        return 'boolean'
    if re.fullmatch('[-+]?\\d+', text):
        return 'integer'
    if re.fullmatch('[-+]?(?:\\d+\\.\\d*|\\d*\\.\\d+)', text):
        return 'float'
    if re.fullmatch('(?:\\d{1,3}\\.){3}\\d{1,3}', text):
        return 'ipv4'
    if re.fullmatch('(?:\\d{1,3}\\.){3}\\d{1,3}/\\d{1,2}', text):
        return 'cidr'
    if re.match('^[a-zA-Z][a-zA-Z0-9+.-]*://', text):
        return 'url'
    if text.startswith('{') and text.endswith('}'):
        return 'object_like'
    if text.startswith('[') and text.endswith(']'):
        return 'list_like'
    if '{{' in text or '${' in text or '<%' in text:
        return 'template'
    return 'string'

def extract_file_extension(file_path):
    text = str(file_path).strip().lower()
    if not text:
        return '<missing>'
    filename = text.replace('\\', '/').split('/')[-1]
    if filename == 'dockerfile':
        return 'dockerfile'
    if filename.startswith('dockerfile.'):
        return 'dockerfile'
    if '.' not in filename:
        return '<no_extension>'
    return filename.rsplit('.', 1)[-1]

def extract_top_level_directory(file_path):
    text = str(file_path).strip().replace('\\', '/')
    segments = [segment for segment in text.split('/') if segment and segment != '.']
    if not segments:
        return '<root>'
    if len(segments) == 1:
        return '<root>'
    return segments[0].lower()

def extract_field_root(field_path):
    text = str(field_path).strip()
    if not text:
        return '<missing>'
    root = re.split('[.\\[]', text, maxsplit=1)[0]
    return root.lower() or '<missing>'

def extract_field_leaf(field_path):
    text = str(field_path).strip()
    if not text:
        return '<missing>'
    normalized = re.sub('\\[\\d+\\]', '', text)
    segments = [segment for segment in normalized.split('.') if segment]
    if not segments:
        return '<missing>'
    return segments[-1].lower()

SECURITY_KEYWORD_PATTERN = '(?:auth|password|passwd|secret|token|credential|certificate|cert|private_key|public_key|permission|role|rbac|security|encrypt|decrypt|tls|ssl)'

NETWORK_KEYWORD_PATTERN = '(?:port|host|hostname|address|ip|cidr|network|ingress|egress|protocol|firewall|acl|listen|bind|route|subnet|gateway|dns)'

RESOURCE_KEYWORD_PATTERN = '(?:cpu|memory|limit|limits|request|requests|quota|replica|replicas|storage|timeout|capacity)'

EXPOSURE_KEYWORD_PATTERN = '(?:public|external|expose|exposed|allow|allowed|anonymous|wildcard|world|internet)'

COMMIT_SECURITY_PATTERN = '(?:security|secure|vulnerability|cve|auth|credential|password|tls|ssl|permission)'

COMMIT_REMOVAL_PATTERN = '(?:remove|removed|delete|deleted|drop|disable|disabled)'

COMMIT_FIX_PATTERN = '(?:fix|fixed|patch|repair|correct|resolve|resolved)'

def engineer_structured_features(dataframe):
    features = pd.DataFrame(index=dataframe.index)
    field_path = normalize_text_series(dataframe['field_path'], STRUCTURED_SETTINGS['maximum_path_processing_length'])
    old_value = normalize_text_series(dataframe['old_value'], STRUCTURED_SETTINGS['maximum_value_processing_length'])
    new_value = normalize_text_series(dataframe['new_value'], STRUCTURED_SETTINGS['maximum_value_processing_length'])
    file_path = normalize_text_series(dataframe['file_path'], STRUCTURED_SETTINGS['maximum_path_processing_length'])
    commit_message = normalize_text_series(dataframe['commit_message'], STRUCTURED_SETTINGS['maximum_commit_message_length'])
    field_lower = field_path.str.lower()
    old_lower = old_value.str.lower()
    new_lower = new_value.str.lower()
    file_lower = file_path.str.lower()
    commit_lower = commit_message.str.lower()
    features['configuration_type'] = dataframe['configuration_type'].fillna('<missing>').astype(str).str.lower()
    features['parser_mode'] = dataframe['parser_mode'].fillna('<missing>').astype(str).str.lower()
    features['operation'] = dataframe['operation'].fillna('<missing>').astype(str).str.lower()
    features['file_extension'] = file_path.apply(extract_file_extension)
    features['top_level_directory'] = file_path.apply(extract_top_level_directory)
    features['field_root'] = field_path.apply(extract_field_root)
    features['field_leaf'] = field_path.apply(extract_field_leaf)
    features['old_value_type'] = old_value.apply(infer_value_type)
    features['new_value_type'] = new_value.apply(infer_value_type)
    features['value_type_transition'] = features['old_value_type'] + '_to_' + features['new_value_type']
    old_missing = old_value.eq('')
    new_missing = new_value.eq('')
    features['presence_transition'] = np.select([old_missing & ~new_missing, ~old_missing & new_missing, old_missing & new_missing], ['missing_to_present', 'present_to_missing', 'missing_to_missing'], default='present_to_present')
    features['field_path_length'] = field_path.str.len()
    features['field_path_depth'] = field_path.str.count('\\.') + field_path.str.count('\\[')
    features['field_segment_count'] = field_path.str.count('\\.') + 1
    features['field_array_index_count'] = field_path.str.count('\\[\\d+\\]')
    features['field_digit_count'] = field_path.str.count('\\d')
    features['field_underscore_count'] = field_path.str.count('_')
    features['field_dash_count'] = field_path.str.count('-')
    features['field_security_keyword_count'] = field_lower.str.count(SECURITY_KEYWORD_PATTERN)
    features['field_network_keyword_count'] = field_lower.str.count(NETWORK_KEYWORD_PATTERN)
    features['field_resource_keyword_count'] = field_lower.str.count(RESOURCE_KEYWORD_PATTERN)
    features['field_exposure_keyword_count'] = field_lower.str.count(EXPOSURE_KEYWORD_PATTERN)
    features['old_value_length'] = old_value.str.len()
    features['new_value_length'] = new_value.str.len()
    features['value_length_change'] = features['new_value_length'] - features['old_value_length']
    features['absolute_value_length_change'] = features['value_length_change'].abs()
    features['old_token_count'] = old_value.str.count('\\S+')
    features['new_token_count'] = new_value.str.count('\\S+')
    features['old_line_count'] = old_value.str.count('\\n') + 1
    features['new_line_count'] = new_value.str.count('\\n') + 1
    features['old_digit_count'] = old_value.str.count('\\d')
    features['new_digit_count'] = new_value.str.count('\\d')
    features['old_alpha_count'] = old_value.str.count('[A-Za-z]')
    features['new_alpha_count'] = new_value.str.count('[A-Za-z]')
    features['old_special_count'] = old_value.str.count('[^A-Za-z0-9\\s]')
    features['new_special_count'] = new_value.str.count('[^A-Za-z0-9\\s]')
    features['old_special_ratio'] = features['old_special_count'] / features['old_value_length'].clip(lower=1)
    features['new_special_ratio'] = features['new_special_count'] / features['new_value_length'].clip(lower=1)
    features['old_character_entropy'] = old_value.apply(character_entropy)
    features['new_character_entropy'] = new_value.apply(character_entropy)
    features['entropy_change'] = features['new_character_entropy'] - features['old_character_entropy']
    features['values_equal'] = old_value.eq(new_value).astype(int)
    features['old_missing'] = old_missing.astype(int)
    features['new_missing'] = new_missing.astype(int)
    ipv4_pattern = '(?:\\b\\d{1,3}\\.){3}\\d{1,3}\\b'
    cidr_pattern = '(?:\\b\\d{1,3}\\.){3}\\d{1,3}/\\d{1,2}\\b'
    url_pattern = '[A-Za-z][A-Za-z0-9+.-]*://'
    template_pattern = '(?:\\{\\{|\\$\\{|<%)'
    environment_pattern = '(?:\\$\\{?[A-Za-z_][A-Za-z0-9_]*\\}?)'
    wildcard_pattern = '(?:\\*|0\\.0\\.0\\.0|::/0)'
    for prefix, text_series in [('old', old_lower), ('new', new_lower)]:
        features[f'{prefix}_contains_ipv4'] = text_series.str.contains(ipv4_pattern, regex=True, na=False).astype(int)
        features[f'{prefix}_contains_cidr'] = text_series.str.contains(cidr_pattern, regex=True, na=False).astype(int)
        features[f'{prefix}_contains_url'] = text_series.str.contains(url_pattern, regex=True, na=False).astype(int)
        features[f'{prefix}_contains_template'] = text_series.str.contains(template_pattern, regex=True, na=False).astype(int)
        features[f'{prefix}_contains_environment_reference'] = text_series.str.contains(environment_pattern, regex=True, na=False).astype(int)
        features[f'{prefix}_contains_wildcard'] = text_series.str.contains(wildcard_pattern, regex=True, na=False).astype(int)
        features[f'{prefix}_security_keyword_count'] = text_series.str.count(SECURITY_KEYWORD_PATTERN)
        features[f'{prefix}_network_keyword_count'] = text_series.str.count(NETWORK_KEYWORD_PATTERN)
        features[f'{prefix}_resource_keyword_count'] = text_series.str.count(RESOURCE_KEYWORD_PATTERN)
        features[f'{prefix}_exposure_keyword_count'] = text_series.str.count(EXPOSURE_KEYWORD_PATTERN)
    old_numeric = pd.to_numeric(old_value, errors='coerce')
    new_numeric = pd.to_numeric(new_value, errors='coerce')
    features['old_is_numeric'] = old_numeric.notna().astype(int)
    features['new_is_numeric'] = new_numeric.notna().astype(int)
    features['old_numeric_log_abs'] = np.log1p(old_numeric.abs())
    features['new_numeric_log_abs'] = np.log1p(new_numeric.abs())
    features['numeric_change'] = new_numeric - old_numeric
    features['numeric_absolute_change'] = features['numeric_change'].abs()
    normalized_file_path = file_path.str.replace('\\', '/', regex=False)
    features['file_path_length'] = normalized_file_path.str.len()
    features['file_path_depth'] = normalized_file_path.str.count('/')
    features['file_hidden_component_count'] = normalized_file_path.str.count('(?:^|/)\\.')
    features['file_test_path_flag'] = file_lower.str.contains('(?:^|/)(?:test|tests|testing)(?:/|$)', regex=True, na=False).astype(int)
    features['file_example_path_flag'] = file_lower.str.contains('(?:example|examples|sample|samples|demo)', regex=True, na=False).astype(int)
    features['file_deployment_path_flag'] = file_lower.str.contains('(?:deploy|deployment|infra|infrastructure|kubernetes|k8s|terraform|ansible|helm)', regex=True, na=False).astype(int)
    features['commit_message_length'] = commit_message.str.len()
    features['commit_message_token_count'] = commit_message.str.count('\\S+')
    features['commit_security_keyword_count'] = commit_lower.str.count(COMMIT_SECURITY_PATTERN)
    features['commit_removal_keyword_count'] = commit_lower.str.count(COMMIT_REMOVAL_PATTERN)
    features['commit_fix_keyword_count'] = commit_lower.str.count(COMMIT_FIX_PATTERN)
    features['commit_revert_flag'] = commit_lower.str.contains('\\brevert(?:ed|ing)?\\b', regex=True, na=False).astype(int)
    features['commit_update_flag'] = commit_lower.str.contains('\\b(?:update|updated|upgrade|bump)\\b', regex=True, na=False).astype(int)
    features.replace([np.inf, -np.inf], np.nan, inplace=True)
    return features
