import click
import subprocess
from sharesphere.database import engine, Base
from sharesphere.models import User, Group
from sharesphere.auth import create_user
from sharesphere.config import load_config, save_config
from omegaconf import OmegaConf
from pathlib import Path
import os

@click.group()
def main():
    """ShareSphere CLI"""
    pass

@main.command()
def init():
    """Initialize the database and create an admin account."""
    # Load configuration
    config = load_config()

    # Prompt for configuration settings
    db_path = click.prompt("Enter the path for the database file", default=config.db.url.replace('sqlite:///', ''))
    db_url = f"sqlite:///{db_path}"
    config.db.url = db_url

    upload_folder = click.prompt("Enter upload folder", default=config.upload.folder)
    config.upload.folder = upload_folder

    log_folder = click.prompt("Enter log folder", default=config.logging.folder)
    config.logging.folder = log_folder

    log_level = click.prompt("Enter log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", default=config.logging.level)
    config.logging.level = log_level

    backup_folder = click.prompt("Enter backup folder", default=config.backup.folder)
    config.backup.folder = backup_folder

    backup_schedule = click.prompt("Enter backup schedule (cron syntax)", default=config.backup.schedule)
    config.backup.schedule = backup_schedule

    # Save updated configuration
    save_config(config)

    # Create necessary directories
    directories = [
        config.upload.folder,
        config.logging.folder,
        config.backup.folder
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        click.echo(f"Created directory: {directory}")

    # Create the database file if it does not exist
    if db_url.startswith('sqlite:///'):
        db_file_path = db_url.replace('sqlite:///', '')
        if not os.path.exists(db_file_path):
            open(db_file_path, 'a').close()
            click.echo(f"Created database file: {db_file_path}")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    click.echo("Database initialized successfully.")

    # Prompt for admin account details
    admin_username = click.prompt("Enter admin username")
    admin_password = click.prompt("Enter admin password", hide_input=True, confirmation_prompt=True)
    admin_user = create_user(admin_username, admin_password, is_admin=True)
    click.echo(f"Admin user '{admin_username}' created successfully.")

    # Prompt for additional users
    while click.confirm("Do you want to create a new user?"):
        username = click.prompt("Enter username")
        password = click.prompt("Enter password", hide_input=True, confirmation_prompt=True)
        create_user(username, password)
        click.echo(f"User '{username}' created successfully.")

@main.command()
@click.option('--config', default=None, help='Path to the configuration file.')
def start(config):
    """Start the ShareSphere application."""
    # Determine the config path
    if config:
        config_path = Path(config).resolve()
    else:
        config_path = Path.cwd() / "config.yaml"
    
    # Check if config.yaml exists
    if not config_path.exists():
        click.echo(f"Error: Configuration file not found at {config_path}")
        return
    
    # Set environment variable for config path
    os.environ["SHARESPHERE_CONFIG_PATH"] = str(config_path)
    
    # Determine the absolute path to app.py relative to cli.py
    app_path = Path(__file__).parent / "app.py"
    
    if not app_path.exists():
        click.echo(f"Error: app.py does not exist at {app_path}")
        return
    
    # Run Streamlit with the absolute path to app.py
    try:
        subprocess.run(["streamlit", "run", str(app_path)], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Failed to start Streamlit. {e}")

if __name__ == "__main__":
    main()
