# sharesphere/config.py

from omegaconf import OmegaConf, DictConfig
import os
from pathlib import Path
import logging
import sys

logger = logging.getLogger(__name__)

def parse_arguments():
    """
    Parse command-line arguments to extract the --config option.
    
    Returns:
        str or None: The path to the configuration file if provided, else None.
    """
    config_path = None
    args = sys.argv[1:]
    if '--config' in args:
        try:
            config_index = args.index('--config')
            config_path = args[config_index + 1]
        except (IndexError, ValueError):
            logger.error("The '--config' option requires a file path.")
            raise ValueError("The '--config' option requires a file path.")
    return config_path

def load_config() -> DictConfig:
    """
    Load configuration using OmegaConf.
    Priority:
        1. User-specified config file via --config
        2. Default config/config.yaml within the package
    
    Returns:
        DictConfig: Configuration object.
    
    Raises:
        FileNotFoundError: If the specified config file does not exist.
        OmegaConf.ConfigError: If the configuration file contains invalid YAML.
    """
    config_path = parse_arguments()
    
    if config_path:
        # User specified a config file
        config_file = Path(config_path)
        if not config_file.is_file():
            error_message = (
                f"⚠️ Configuration file '{config_file}' not found.\n"
                "Please provide a valid path to your 'config.yaml'."
            )
            logger.error(error_message)
            raise FileNotFoundError(error_message)
        try:
            user_config = OmegaConf.load(config_file)
            logger.info(f"Configuration loaded successfully from '{config_file}'.")
            return user_config
        except Exception as e:
            error_message = f"❌ Failed to load configuration from '{config_file}': {e}"
            logger.error(error_message)
            raise OmegaConf.ConfigError(error_message)
    else:
        # Load default config from package
        default_config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        if not default_config_path.is_file():
            error_message = (
                f"⚠️ Default configuration file '{default_config_path}' not found.\n"
                "Please provide a 'config.yaml' in the 'config/' directory or specify one using the '--config' option."
            )
            logger.error(error_message)
            raise FileNotFoundError(error_message)
        try:
            default_config = OmegaConf.load(default_config_path)
            logger.info(f"Default configuration loaded successfully from '{default_config_path}'.")
            return default_config
        except Exception as e:
            error_message = f"❌ Failed to load default configuration from '{default_config_path}': {e}"
            logger.error(error_message)
            raise OmegaConf.ConfigError(error_message)