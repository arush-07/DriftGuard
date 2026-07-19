import json
import math
import re
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

RANDOM_SEED = 42

# Runtime-safe Transformer settings
TRAIN_BATCH_SIZE = 2
EVALUATION_BATCH_SIZE = 8
GRADIENT_ACCUMULATION_STEPS = 8


TRANSFORMER_SETTINGS = {'random_seed': RANDOM_SEED, 'pretrained_model_name': 'huggingface/CodeBERTa-small-v1', 'class_order': ['benign', 'low', 'medium', 'high', 'critical'], 'maximum_sequence_length': 256, 'maximum_field_path_characters': 1000, 'maximum_old_value_characters': 1500, 'maximum_new_value_characters': 1500, 'maximum_file_path_characters': 1000, 'maximum_commit_message_characters': 800, 'learning_rate': 2e-05, 'weight_decay': 0.01, 'number_of_epochs': 5, 'warmup_ratio': 0.1, 'training_batch_size': TRAIN_BATCH_SIZE, 'evaluation_batch_size': EVALUATION_BATCH_SIZE, 'gradient_accumulation_steps': GRADIENT_ACCUMULATION_STEPS, 'early_stopping_patience': 2, 'early_stopping_threshold': 0.001, 'maximum_gradient_norm': 1.0, 'metric_for_best_model': 'macro_f1', 'additional_special_tokens': ['[FIELD]', '[OLD]', '[NEW]', '[CONFIG_TYPE]', '[OPERATION]', '[PARSER]', '[FILE]', '[COMMIT]']}

TRANSFORMER_RAW_FEATURE_COLUMNS = ['field_path', 'old_value', 'new_value', 'configuration_type', 'operation', 'parser_mode', 'file_path', 'commit_message']

def normalize_text_value(value, maximum_characters):
    if pd.isna(value):
        return '<MISSING>'
    text = str(value)
    text = text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    text = ' '.join(text.split())
    if not text:
        return '<EMPTY>'
    return text[:maximum_characters]

def build_transformer_text(dataframe):
    generated_text = []
    for record in dataframe[TRANSFORMER_RAW_FEATURE_COLUMNS].to_dict(orient='records'):
        field_path = normalize_text_value(record.get('field_path'), TRANSFORMER_SETTINGS['maximum_field_path_characters'])
        old_value = normalize_text_value(record.get('old_value'), TRANSFORMER_SETTINGS['maximum_old_value_characters'])
        new_value = normalize_text_value(record.get('new_value'), TRANSFORMER_SETTINGS['maximum_new_value_characters'])
        configuration_type = normalize_text_value(record.get('configuration_type'), 200)
        operation = normalize_text_value(record.get('operation'), 100)
        parser_mode = normalize_text_value(record.get('parser_mode'), 100)
        file_path = normalize_text_value(record.get('file_path'), TRANSFORMER_SETTINGS['maximum_file_path_characters'])
        commit_message = normalize_text_value(record.get('commit_message'), TRANSFORMER_SETTINGS['maximum_commit_message_characters'])
        combined_text = f'[FIELD] {field_path} [OLD] {old_value} [NEW] {new_value} [CONFIG_TYPE] {configuration_type} [OPERATION] {operation} [PARSER] {parser_mode} [FILE] {file_path} [COMMIT] {commit_message}'
        generated_text.append(combined_text)
    return pd.Series(generated_text, index=dataframe.index, dtype='string')
