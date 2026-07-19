import json
import math
import re
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

BASELINE_SETTINGS = {'random_seed': 42, 'class_order': ['benign', 'low', 'medium', 'high', 'critical'], 'word_max_features': 60000, 'character_max_features': 80000, 'word_ngram_range': [1, 2], 'character_ngram_range': [3, 5], 'minimum_document_frequency': 2, 'maximum_document_frequency': 0.995, 'maximum_field_path_length': 1000, 'maximum_value_length': 1500, 'maximum_file_path_length': 1000, 'maximum_commit_message_length': 1500, 'model_selection_metrics': ['macro_f1', 'critical_recall', 'high_critical_recall', 'balanced_accuracy']}

BASELINE_RAW_FEATURE_COLUMNS = ['field_path', 'old_value', 'new_value', 'configuration_type', 'operation', 'parser_mode', 'file_path', 'commit_message']

def clean_text_value(value, maximum_length):
    if pd.isna(value):
        return '<MISSING>'
    text = str(value)
    text = text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    text = ' '.join(text.split())
    if len(text) > maximum_length:
        text = text[:maximum_length]
    return text

def build_baseline_text(dataframe):
    text_records = []
    for record in dataframe[BASELINE_RAW_FEATURE_COLUMNS].to_dict(orient='records'):
        field_path = clean_text_value(record.get('field_path'), BASELINE_SETTINGS['maximum_field_path_length'])
        old_value = clean_text_value(record.get('old_value'), BASELINE_SETTINGS['maximum_value_length'])
        new_value = clean_text_value(record.get('new_value'), BASELINE_SETTINGS['maximum_value_length'])
        configuration_type = clean_text_value(record.get('configuration_type'), 200)
        operation = clean_text_value(record.get('operation'), 100)
        parser_mode = clean_text_value(record.get('parser_mode'), 100)
        file_path = clean_text_value(record.get('file_path'), BASELINE_SETTINGS['maximum_file_path_length'])
        commit_message = clean_text_value(record.get('commit_message'), BASELINE_SETTINGS['maximum_commit_message_length'])
        combined_text = ' '.join([f'FIELD_PATH={field_path}', f'OLD_VALUE={old_value}', f'NEW_VALUE={new_value}', f'CONFIG_TYPE={configuration_type}', f'OPERATION={operation}', f'PARSER_MODE={parser_mode}', f'FILE_PATH={file_path}', f'COMMIT_MESSAGE={commit_message}'])
        text_records.append(combined_text)
    return pd.Series(text_records, index=dataframe.index, dtype='string')
