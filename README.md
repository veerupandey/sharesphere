# ShareSphere

ShareSphere is a multi-user file sharing system built with Streamlit, SQLAlchemy, and SQLite. It allows users to upload, share, and download files within a group or with specific users.

## Features

- User authentication and authorization
- File upload and download
- File sharing with groups or specific users
- Admin panel for managing users, files, and groups

## What ShareSphere Can Do

### User Features

- **Login and Logout**: Secure authentication for users to access the system.
- **Upload Files**: Users can upload files and add comments.
- **Download Files**: Users can download files they have uploaded or that have been shared with them.
- **Share Files**: Users can share files with specific users or groups.
- **View Shared Files**: Users can view files shared with them by others.
- **Group Management**: Users can view and request to join groups.
- **User Settings**: Users can change their password.

### Admin Features

- **Manage Users**: Admins can create, delete, and reset passwords for users.
- **Manage Files**: Admins can view and delete any files uploaded by users.
- **Manage Groups**: Admins can create and manage user groups.
- **View Logs**: Admins can view system logs to monitor activities and troubleshoot issues.
- **Approve/Reject Group Requests**: Admins can approve or reject user requests to join groups.

## Setup

### Prerequisites

- Python 3.8 or higher

### Installation

#### Using pip

1. Install the ShareSphere package using pip:

```sh
pip install sharesphere
```

2. Initialize the database and create an admin account:

```sh
sharesphere init
```

During initialization, you will be prompted to provide configuration details such as database URL, upload folder, log folder, log level, backup folder, and backup schedule. These details will be saved to a `config.yaml` file.

3. Start the ShareSphere application:

```sh
sharesphere start
```

4. Open your web browser and navigate to `http://localhost:8501` to access the ShareSphere application.

#### Using Poetry for Development or Building from Source

1. Clone the repository:

```sh
git clone https://github.com/veerupandey/sharesphere.git
cd sharesphere
```

2. Install the required packages using Poetry:

```sh
poetry install
```

3. Initialize the database:

```sh
poetry run sharesphere init
```

4. Run the Streamlit application:

```sh
poetry run streamlit run sharesphere/app.py
```

5. Open your web browser and navigate to `http://localhost:8501` to access the ShareSphere application.

## Project Structure

```
sharesphere/
├── admin.py
├── app.py
├── auth.py
├── cli.py
├── config.py
├── database.py
├── file_manager.py
├── models.py
└── README.md
```

- `admin.py`: Admin functionalities for managing users, files, and groups.
- `app.py`: Main Streamlit application.
- `auth.py`: Authentication and authorization logic.
- `cli.py`: Command-line interface for initialization and starting the application.
- `config.py`: Configuration settings.
- `database.py`: Database setup and connection.
- `file_manager.py`: File upload, download, and management logic.
- `models.py`: SQLAlchemy models for the database.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or suggestions, please contact [rakeshpandey820@gmail.com](mailto:rakeshpandey820@gmail.com).