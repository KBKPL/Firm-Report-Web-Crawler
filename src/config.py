import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

def load_config() -> dict:
    """Load configuration from config.json."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_company_config(company_name: str) -> dict:
    """Get configuration dict for a given company."""
    config = load_config()
    return config.get(company_name, {})
