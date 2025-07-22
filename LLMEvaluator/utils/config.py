# llm_evaluator/utils/config.py

import json

def load_config(config_path: str) -> dict:
    """
    Load configuration settings from a JSON file.
    
    :param config_path: Path to the configuration file.
    :return: Dictionary of configuration parameters.
    """
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config
