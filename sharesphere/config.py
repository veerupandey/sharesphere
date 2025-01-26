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

def load_config(config_path: str = None) -> DictConfig:
    """
    Load configuration using OmegaConf.
    Priority:
        1. User-specified config file via --config
        2. config.yaml in the current working directory
        3. Default sharesphere/config.yaml within the package
    
    Returns:
        DictConfig: Configuration object.
    
    Raises:
        FileNotFoundError: If the specified config file does not exist.
        OmegaConf.ConfigError: If the configuration file contains invalid YAML.
    """
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
        # Load config from current working directory
        cwd_config_path = Path(os.getcwd()) / "config.yaml"
        if cwd_config_path.is_file():
            try:
                user_config = OmegaConf.load(cwd_config_path)
                logger.info(f"Configuration loaded successfully from '{cwd_config_path}'.")
                return user_config
            except Exception as e:
                error_message = f"❌ Failed to load configuration from '{cwd_config_path}': {e}"
                logger.error(error_message)
                raise OmegaConf.ConfigError(error_message)
        
        # Load default config from package
        default_config_path = Path(__file__).parent / "config.yaml"
        if not default_config_path.is_file():
            error_message = (
                f"⚠️ Default configuration file '{default_config_path}' not found.\n"
                "Please provide a 'config.yaml' in the 'sharesphere/' directory or specify one using the '--config' option."
            )
            logger.error(error_message)
            raise FileNotFoundError(error_message)
        try:
            default_config = OmegaConf.load(default_config_path)
            logger.info(f"Default configuration loaded successfully from '{default_config_path}'.")
            
            # Ensure the database URL is set correctly
            if 'db' in default_config and 'url' in default_config.db:
                db_url = default_config.db.url
                if db_url.startswith('sqlite:///'):
                    db_path = db_url.replace('sqlite:///', '')
                    if not os.path.isabs(db_path):
                        db_path = os.path.join(os.getcwd(), db_path)
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    default_config.db.url = f"sqlite:///{db_path}"
            
            return default_config
        except Exception as e:
            error_message = f"❌ Failed to load default configuration from '{default_config_path}': {e}"
            logger.error(error_message)
            raise OmegaConf.ConfigError(error_message)

def save_config(config: DictConfig, config_path: str = None):
    """
    Save the configuration to a file.
    
    Args:
        config (DictConfig): Configuration object to save.
        config_path (str, optional): Path to save the configuration file. Defaults to None.
    """
    if not config_path:
        config_path = Path(os.getcwd()) / "config.yaml"
    OmegaConf.save(config, config_path)
    logger.info(f"Configuration saved to '{config_path}'.")