import toml
import logging
import os
logger = logging.getLogger(__name__)

def parse_toml_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return toml.loads(f.read())
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except toml.TomlDecodeError as e:
        logger.error(f"Error parsing toml file: {e}")
        return None

def get_config():
    return parse_toml_file("config.toml")

def check_env_vars():
    env_vars = [
        'GOOGLE_API_KEY',
        'PROJECT_ID',
        'DATABASE_URL'
    ]
    for var in env_vars:
        if var not in os.environ:
            logger.error(f"Environment variable not set: {var}")
            return False
    return True
