import streamlit as st
import logging
import os
import base64
import pandas as pd
from omegaconf import DictConfig
from sqlalchemy.orm import joinedload
from sharesphere.auth import authenticate_user, get_user_by_username
from sharesphere.file_manager import upload_file, get_shared_files, delete_file
from sharesphere.admin import (
    list_users,
    create_new_user,
    delete_user,
    reset_user_password,
    get_system_logs,
    list_groups,
    create_new_group,
    list_group_requests,
    approve_group_request,
    reject_group_request,
)
from sharesphere.config import load_config
from sharesphere.database import SessionLocal
from sharesphere.models import User, Group, GroupRequest, File  # Ensure File is imported

# === Streamlit Configuration ===
st.set_page_config(
    page_title="ShareSphere",
    layout="wide",
    page_icon="📁",
    initial_sidebar_state="expanded",
)

# === Load Configuration ===
config: DictConfig = load_config()

# === Initialize Logging ===
logger = logging.getLogger(__name__)

def setup_logging(config: DictConfig):
    """Setup logging configuration."""
    log_dir = config.logging.folder
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')
    if not os.path.exists(log_file):
        with open(log_file, 'w'):
            pass
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(getattr(logging, config.logging.level.upper(), logging.INFO))


setup_logging(config)

# === Session State Initialization ===
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = None
    st.session_state['is_admin'] = False
    st.session_state['dark_mode'] = False  # Initialize dark mode preference

# === Custom CSS Styling ===
def inject_css(dark_mode=False):
    """Inject custom CSS and JavaScript for Dark Mode toggling."""
    css = """
    <style>
    /* Center Align Titles */
    .css-18e3th9 h1 {
        text-align: center;
        color: #4B0082; /* Indigo */
    }
    .css-18e3th9 h2 {
        color: #483D8B; /* Dark Slate Blue */
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #F5F5F5; /* Light Gray */
    }

    /* Button Styling */
    .css-1aumxhk.edgvbvh3 {
        background-color: #6A5ACD; /* Slate Blue */
        color: white;
        border-radius: 8px;
    }
    .css-1aumxhk.edgvbvh3:hover {
        background-color: #836FFF; /* Light Slate Blue */
    }

    /* DataFrame Styling */
    .stDataFrame table {
        border-collapse: collapse;
    }
    .stDataFrame th, .stDataFrame td {
        border: 1px solid #ddd;
        padding: 8px;
    }
    .stDataFrame tr:nth-child(even){background-color: #f2f2f2;}
    .stDataFrame tr:hover {background-color: #ddd;}
    .stDataFrame th {
        padding-top: 12px;
        padding-bottom: 12px;
        text-align: left;
        background-color: #4B0082;
        color: white;
    }

    /* Tooltip Styling */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted black; /* If you want dots under the hoverable text */
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 220px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px 0;
        position: absolute;
        z-index: 1;
        bottom: 125%; /* Position above the text */
        left: 50%;
        margin-left: -110px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .tooltip .tooltiptext::after {
        content: "";
        position: absolute;
        top: 100%; /* At the bottom of the tooltip */
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #555 transparent transparent transparent;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    /* Header Image Styling */
    .header-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 150px;
    }

    /* Dark Mode Styles */
    body.dark-mode, .css-18e3th9.dark-mode, .css-1d391kg.dark-mode {
        background-color: #121212 !important;
        color: #FFFFFF !important;
    }
    .dark-mode .css-1aumxhk.edgvbvh3 {
        background-color: #333333 !important;
        color: #FFFFFF !important;
    }
    .dark-mode .stDataFrame th {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
    }
    .dark-mode .stDataFrame tr:nth-child(even){
        background-color: #1A1A1A !important;
    }
    .dark-mode .stDataFrame tr:hover {
        background-color: #333333 !important;
    }
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

    if dark_mode:
        # Inject JavaScript to add 'dark-mode' class
        js = """
        <script>
        if (!document.body.classList.contains('dark-mode')) {
            document.body.classList.add('dark-mode');
        }
        </script>
        """
    else:
        # Inject JavaScript to remove 'dark-mode' class
        js = """
        <script>
        if (document.body.classList.contains('dark-mode')) {
            document.body.classList.remove('dark-mode');
        }
        </script>
        """

    st.markdown(js, unsafe_allow_html=True)

inject_css()

# === Header with Logo and Welcome Message ===
def display_header():
    """Display the header with logo and welcome messages."""
    st.image(
        "https://via.placeholder.com/150",
        width=150,
        use_container_width=False,  # Replaced the deprecated use_column_width parameter
        output_format="PNG"
    )  # Replace with your logo URL or local path
    st.markdown("---")
    st.markdown("<h1>🔒 ShareSphere</h1>", unsafe_allow_html=True)
    st.markdown("<h2>The Ultimate Multi-User File Sharing Platform</h2>", unsafe_allow_html=True)
    st.markdown("---")


# === Login Interface ===
def login():
    """Render the login interface."""
    display_header()
    st.write("### Please enter your credentials to access the system.")

    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username", placeholder="Enter your username")
        with col2:
            password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", type="primary")

    if submit:
        auth_status, is_admin = authenticate_user(username, password)
        if auth_status:
            user = get_user_by_username(username)
            st.session_state['authentication_status'] = True
            st.session_state['user_id'] = user.id
            st.session_state['username'] = user.username
            st.session_state['is_admin'] = is_admin
            st.session_state['dark_mode'] = user.dark_mode_pref  # Load user preference
            st.success(f"✅ Logged in as **{username}**!")
            logger.info(f"User '{username}' logged in.")
            # Re-inject CSS based on preference
            inject_css(dark_mode=user.dark_mode_pref)
        else:
            st.error("⚠️ Incorrect username or password.")
            logger.warning(f"Failed login attempt for username '{username}'.")


# === Logout Function ===
def logout():
    """Handle user logout."""
    st.session_state['authentication_status'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = None
    st.session_state['is_admin'] = False
    st.session_state['dark_mode'] = False
    st.success("✅ Logged out successfully.")
    logger.info("User logged out.")
    # Refresh the app by clearing the cache (as a workaround since we can't rerun)
    st.experimental_set_query_params()  # Reset query parameters to force rerun


# === Function to Generate Download Links ===
def get_download_link(file_path, filename):
    """
    Generate a download link for a given file with appropriate MIME type.

    Args:
        file_path (str): Path to the file.
        filename (str): Name of the file.

    Returns:
        str: HTML anchor tag for downloading the file.
    """
    try:
        with open(file_path, "rb") as f:
            bytes_data = f.read()
        encoded = base64.b64encode(bytes_data).decode()

        # Determine MIME type based on file extension
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            mime = 'image/jpeg'
        elif filename.lower().endswith('.pdf'):
            mime = 'application/pdf'
        else:
            mime = 'application/octet-stream'

        href = f'<a href="data:{mime};base64,{encoded}" download="{filename}">📥 Download {filename}</a>'
        return href
    except Exception as e:
        logger.error(f"Error generating download link for {filename}: {e}")
        return "Error generating link."


# === Upload Interface with Interactive Elements ===
def upload_interface(user_id, username):
    """Provide the interface for users to upload files."""
    st.header("📤 Upload Files")
    st.markdown("<style> .big-font {font-size:20px !important;}</style>", unsafe_allow_html=True)
    st.markdown('<p class="big-font">Upload your files and share them with your team seamlessly.</p>', unsafe_allow_html=True)

    # Upload Options with Icons
    share_option = st.radio(
        "Share Options",
        ("Share with Group", "Share with Specific Users"),
        format_func=lambda x: f"📂 {x}",
    )

    # Fetch users and groups for sharing
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    user_groups = user.groups
    group_ids = [group.id for group in user_groups]

    users = db.query(User).filter(User.id != user_id).all()
    groups = db.query(Group).filter(Group.id.in_(group_ids)).all()
    db.close()

    with st.expander("🤔 Need Help?", expanded=True):
        st.write("""
            - **Share with Group:** Share files with all members of your existing groups.
            - **Share with Specific Users:** Select individual users to share your files with.
        """)

    if share_option == "Share with Specific Users":
        selected_users = st.multiselect(
            "Select Users to Share With",
            [user.username for user in users],
            help="Choose individual users to share your files with."
        )
        selected_groups = []
    else:
        selected_groups = st.multiselect(
            "Select Groups to Share With",
            [group.name for group in groups],
            help="Choose groups to share your files with."
        )
        selected_users = []

    uploaded_files = st.file_uploader(
        "Select files to upload",
        type=None,
        accept_multiple_files=True,
        help="Upload multiple files by holding down the Ctrl or Command key.",
        key="upload_files"
    )
    file_comment = st.text_area(
        "Add a comment about the file (optional)",
        max_chars=200,
        help="Provide a brief description or note about the uploaded files."
    )

    if uploaded_files:
        db = SessionLocal()
        if share_option == "Share with Specific Users":
            selected_user_objs = db.query(User).filter(User.username.in_(selected_users)).all()
            selected_user_ids = [user.id for user in selected_user_objs]
            selected_group_ids = []
        else:
            selected_group_objs = db.query(Group).filter(Group.name.in_(selected_groups)).all()
            selected_group_ids = [group.id for group in selected_group_objs]
            selected_user_ids = []
        db.close()

        for uploaded_file in uploaded_files:
            success, message = upload_file(
                uploader_id=user_id,
                uploader_name=username,
                file_storage=uploaded_file,
                file_comment=file_comment,
                shared_with_group=(share_option == "Share with Group"),
                shared_users=selected_user_ids,
                shared_groups=selected_group_ids
            )
            if success:
                st.success(f"✅ {uploaded_file.name} uploaded successfully.")
                logger.info(f"User '{username}' uploaded file '{uploaded_file.name}'.")
            else:
                st.error(f"❌ Failed to upload {uploaded_file.name}.")
                logger.error(f"User '{username}' failed to upload file '{uploaded_file.name}': {message}")


# === Download Interface with Interactive Features ===
def download_interface(user_id):
    """Provide the interface for users to download files."""
    st.header("📥 Download Files")
    st.markdown("<style> .big-font {font-size:20px !important;}</style>", unsafe_allow_html=True)
    st.markdown('<p class="big-font">Access and download files shared with you or uploaded by you.</p>', unsafe_allow_html=True)

    own_files, shared_files = get_shared_files(user_id)

    # Your Files Section
    st.subheader("🔄 Your Files")
    if own_files:
        for file in own_files:
            file_path = file.filepath
            filename = file.filename
            comment = file.comment if hasattr(file, 'comment') else ""  # Safely get comment
            st.markdown(f"### {filename}")
            download_link = get_download_link(file_path, filename)
            st.markdown(download_link, unsafe_allow_html=True)

            # Preview based on file type
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    st.image(file_path, width=300, caption=comment)
                except Exception as e:
                    st.error(f"❌ Failed to load image `{filename}`.")
                    logger.error(f"Error loading image '{filename}': {e}")
            elif filename.lower().endswith('.pdf'):
                try:
                    with open(file_path, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Failed to load PDF `{filename}`.")
                    logger.error(f"Error loading PDF '{filename}': {e}")
            st.markdown("---")
    else:
        st.info("📁 You have not uploaded any files yet.")

    # Shared Files Section
    st.subheader("🔗 Shared Files")
    if shared_files:
        for file in shared_files:
            file_path = file.filepath
            filename = file.filename
            owner = file.owner.username
            comment = file.comment if hasattr(file, 'comment') else ""
            st.markdown(f"### {filename} (Shared by {owner})")
            download_link = get_download_link(file_path, filename)
            st.markdown(download_link, unsafe_allow_html=True)

            # Notify sender upon download
            download_button = st.button(f"Download {filename}", key=f"download_{file.id}")
            if download_button:
                notify_sender(file.owner_id, user_id, filename)
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="Confirm Download",
                        data=f,
                        file_name=filename,
                        key=f"confirm_download_{file.id}"
                    )

            # Preview based on file type
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    st.image(file_path, width=300, caption=comment)
                except Exception as e:
                    st.error(f"❌ Failed to load image `{filename}`.")
                    logger.error(f"Error loading image '{filename}': {e}")
            elif filename.lower().endswith('.pdf'):
                try:
                    with open(file_path, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Failed to load PDF `{filename}`.")
                    logger.error(f"Error loading PDF '{filename}': {e}")
            st.markdown("---")
    else:
        st.info("📁 No files have been shared with you yet.")


def notify_sender(sender_id, downloader_id, filename):
    """Notify the sender that their file has been downloaded."""
    db = SessionLocal()
    sender = db.query(User).filter(User.id == sender_id).first()
    downloader = db.query(User).filter(User.id == downloader_id).first()
    if sender and downloader:
        message = f"📣 Your file '{filename}' was downloaded by {downloader.username}."
        logger.info(message)
        # TODO: Integrate email notifications or in-app notifications to the sender
    db.close()


# === Admin Panel Interface with Enhanced Features ===
def admin_interface():
    """Provide the admin panel for managing users, files, groups, and logs."""
    st.header("🛠️ Admin Panel")
    st.markdown("<style> .big-font {font-size:20px !important;}</style>", unsafe_allow_html=True)
    st.markdown('<p class="big-font">Manage users, files, groups, and monitor system logs seamlessly.</p>', unsafe_allow_html=True)

    # Tabs for different admin functionalities with Icons
    admin_tabs = st.tabs(["👥 Manage Users", "📂 Manage Files", "👥 Manage Groups", "📈 View Logs"])

    # === Manage Users Tab ===
    with admin_tabs[0]:
        st.subheader("👥 Manage Users")
        st.markdown("Manage all user accounts, including creating, deleting, and resetting passwords.")

        # List all users
        users = list_users()
        if users:
            user_data = {
                "ID": [user.id for user in users],
                "Username": [user.username for user in users],
                "Role": ["Admin" if user.is_admin else "User" for user in users],
                "Created At": [user.created_at.strftime("%Y-%m-%d %H:%M:%S") for user in users]
            }
            df_users = pd.DataFrame(user_data)
            st.dataframe(df_users, use_container_width=True)
        else:
            st.info("📁 No users found.")

        st.write("---")

        # Create New User with Columns
        st.subheader("➕ Create New User")
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username", placeholder="Enter username")
            with col2:
                new_password = st.text_input("Password", type="password", placeholder="Enter password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            is_admin = st.checkbox("Is Admin?", help="Check if the user should have admin privileges.")
            create_submit = st.form_submit_button("Create User", type="primary")

        if create_submit:
            if not new_username or not new_password:
                st.error("❌ Username and password cannot be empty.")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match.")
            else:
                user = create_new_user(new_username, new_password, is_admin)
                if user:
                    st.success(f"✅ User '{new_username}' created successfully.")
                else:
                    st.error(f"❌ User '{new_username}' already exists.")

        st.write("---")

        # Delete Existing User
        st.subheader("🗑️ Delete User")
        with st.form("delete_user_form"):
            user_to_delete = st.selectbox(
                "Select User to Delete",
                [user.username for user in users],
                help="Select a user to remove from the system."
            )
            delete_submit = st.form_submit_button("Delete User", type="primary")

        if delete_submit:
            user = get_user_by_username(user_to_delete)
            if user:
                success, message = delete_user(user.id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("❌ Selected user does not exist.")

        st.write("---")

        # Reset User Password
        st.subheader("🔄 Reset User Password")
        with st.form("reset_password_form"):
            user_for_reset = st.selectbox(
                "Select User",
                [user.username for user in users],
                help="Select a user whose password you want to reset."
            )
            new_pwd = st.text_input("New Password", type="password", placeholder="Enter new password")
            confirm_new_pwd = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
            reset_submit = st.form_submit_button("Reset Password", type="primary")

        if reset_submit:
            if not new_pwd:
                st.error("❌ New password cannot be empty.")
            elif new_pwd != confirm_new_pwd:
                st.error("❌ Passwords do not match.")
            else:
                user = get_user_by_username(user_for_reset)
                success, message = reset_user_password(user.id, new_pwd)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # === Manage Files Tab ===
    with admin_tabs[1]:
        st.subheader("📂 Manage Files")
        st.markdown("Oversee all uploaded files, including deleting unauthorized or unnecessary files.")

        # Display all files
        db = SessionLocal()
        all_files = db.query(File).options(joinedload(File.owner)).all()
        db.close()

        if all_files:
            file_data = {
                "ID": [file.id for file in all_files],
                "Filename": [file.filename for file in all_files],
                "Owner": [file.owner.username for file in all_files],
                "Uploaded At": [file.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") for file in all_files]
            }
            df_files = pd.DataFrame(file_data)
            st.dataframe(df_files, use_container_width=True)

            st.write("---")

            # Delete File
            st.subheader("🗑️ Delete File")
            with st.form("delete_file_form"):
                file_options = [f"{file.filename} (Owner: {file.owner.username})" for file in all_files]
                file_to_delete = st.selectbox(
                    "Select File to Delete",
                    file_options,
                    help="Choose a file to remove from the system."
                )
                delete_file_submit = st.form_submit_button("Delete File", type="primary")

            if delete_file_submit:
                file_id = all_files[file_options.index(file_to_delete)].id
                success, message = delete_file(
                    file_id,
                    user_id=st.session_state["user_id"],
                    admin=True
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
        else:
            st.info("📁 No files uploaded yet.")

    # === Manage Groups Tab ===
    with admin_tabs[2]:
        st.subheader("👥 Manage Groups")
        st.markdown("Create, view, and manage user groups to streamline collaboration.")

        # List all groups
        groups = list_groups()
        if groups:
            group_data = {
                "ID": [group.id for group in groups],
                "Name": [group.name for group in groups],
                "Created At": [group.created_at.strftime("%Y-%m-%d %H:%M:%S") for group in groups]
            }
            df_groups = pd.DataFrame(group_data)
            st.dataframe(df_groups, use_container_width=True)
        else:
            st.info("📁 No groups found.")

        st.write("---")

        # Create New Group
        st.subheader("➕ Create New Group")
        with st.form("create_group_form"):
            new_group_name = st.text_input("Group Name", placeholder="Enter group name")
            create_group_submit = st.form_submit_button("Create Group", type="primary")

        if create_group_submit:
            if not new_group_name:
                st.error("❌ Group name cannot be empty.")
            else:
                group = create_new_group(new_group_name)
                if group:
                    st.success(f"✅ Group '{new_group_name}' created successfully.")
                else:
                    st.error(f"❌ Group '{new_group_name}' already exists.")

        st.write("---")

        # Handle Group Requests
        st.subheader("📩 Group Join Requests")
        admin_group_requests_interface()

    # === View Logs Tab ===
    with admin_tabs[3]:
        st.subheader("📈 View Logs")
        st.markdown("Monitor system activities and troubleshoot issues effectively.")

        log_file = os.path.join(config.logging.folder, "app.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    logs = f.readlines()
                # Display last 200 log entries
                log_text = "".join(logs[-200:])
                st.text_area("Application Logs", log_text, height=600)
            except Exception as e:
                st.error(f"❌ Failed to load logs: {e}")
                logger.error(f"Error loading logs: {e}")
        else:
            st.info("📜 No logs available.")


# === User Settings Interface ===
def user_settings_interface(user_id: int):
    """
    Provide a user-specific settings page where individual users
    (not just admins) can toggle preferences and reset their passwords.
    """
    st.header("⚙️ User Settings")
    st.markdown("Adjust your personal settings, such as interface theme, password, etc.")

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    # -------------- Dark Mode Toggle -------------- #
    st.subheader("Appearance")
    # Check if dark_mode_pref is stored in the user’s DB entry
    current_dark_mode = user.dark_mode_pref if hasattr(user, "dark_mode_pref") else False

    # Provide a checkbox for toggling dark mode
    dark_mode_enabled = st.checkbox(
        "Enable Dark Mode",
        value=current_dark_mode,
        help="Toggle dark mode for a more comfortable low-light experience."
    )

    # If user toggles the checkbox, update the database and apply CSS
    if dark_mode_enabled != current_dark_mode:
        # Update DB
        user.dark_mode_pref = dark_mode_enabled
        db.commit()
        db.refresh(user)
        st.session_state['dark_mode'] = dark_mode_enabled  # Update session state
        inject_css(dark_mode=dark_mode_enabled)  # Apply CSS

    # Inject custom CSS if dark mode is on or off
    inject_css(dark_mode=st.session_state['dark_mode'])

    st.write("---")

    # -------------- Password Reset -------------- #
    st.subheader("Change Your Password")

    with st.form("user_password_change_form"):
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password")

    if submitted:
        # Validate old password, check that new matches confirm
        if not old_password or not new_password or not confirm_new_password:
            st.error("⚠️ All fields are required.")
        elif new_password != confirm_new_password:
            st.error("⚠️ New passwords do not match.")
        else:
            # Reuse existing logic to check hashed password, etc.
            authenticated, _ = authenticate_user(user.username, old_password)
            if authenticated:
                success, message = reset_user_password(user.id, new_password)
                if success:
                    st.success("✅ Password changed successfully!")
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Current password is incorrect.")

    db.close()


# === Admin Group Requests Interface ===
def admin_group_requests_interface():
    """Allow admins to manage user requests to join groups."""
    st.subheader("📩 Group Join Requests")
    st.markdown("Review and manage user requests to join groups.")

    db = SessionLocal()
    requests = db.query(GroupRequest).options(
        joinedload(GroupRequest.user), joinedload(GroupRequest.group)
    ).all()
    db.close()

    if requests:
        request_data = {
            "ID": [request.id for request in requests],
            "User": [request.user.username for request in requests],
            "Group": [request.group.name for request in requests],
            "Status": [request.status for request in requests],
            "Requested At": [request.created_at.strftime("%Y-%m-%d %H:%M:%S") for request in requests],
        }
        df_requests = pd.DataFrame(request_data)
        st.dataframe(df_requests, use_container_width=True)

        st.write("---")

        # Approve or Reject Requests
        st.subheader("Approve or Reject Requests")
        with st.form("approve_reject_form"):
            request_id = st.selectbox(
                "Select Request ID",
                request_data["ID"],
                help="Choose the request ID you want to process."
            )
            action = st.radio(
                "Action",
                ["Approve", "Reject"],
                horizontal=True,
                help="Approve to grant group access or Reject to deny the request."
            )
            action_submit = st.form_submit_button("Submit Action", type="primary")

        if action_submit:
            if action == "Approve":
                success, message = approve_group_request(request_id)
            else:
                success, message = reject_group_request(request_id)
            if success:
                st.success(message)
            else:
                st.error(message)
    else:
        st.info("📁 No group requests found.")


# === User Group Interface ===
def user_groups_interface(user_id):
    """Allow users to view and manage their group memberships."""
    st.header("👥 Your Groups")
    st.markdown("<style> .big-font {font-size:20px !important;}</style>", unsafe_allow_html=True)
    st.markdown('<p class="big-font">Manage your group memberships and collaborate with your peers.</p>', unsafe_allow_html=True)

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    groups = user.groups
    db.close()

    if groups:
        group_data = {
            "ID": [group.id for group in groups],
            "Name": [group.name for group in groups],
            "Joined At": [
                group.created_at.strftime("%Y-%m-%d %H:%M:%S") for group in groups
            ],
        }
        df_groups = pd.DataFrame(group_data)
        st.dataframe(df_groups, use_container_width=True)
    else:
        st.info("📁 You have not joined any groups yet.")

    st.write("---")

    # Request to join a new group
    st.subheader("➕ Request to Join Group")
    available_groups = list_groups()
    # Exclude groups the user is already a part of
    available_group_names = [
        group.name for group in available_groups if group not in groups
    ]
    if available_group_names:
        selected_group = st.selectbox(
            "Select Group to Join",
            available_group_names,
            help="Choose a group you wish to join."
        )
        request_submit = st.button("Request to Join", type="primary")

        if request_submit:
            db = SessionLocal()
            group = db.query(Group).filter(Group.name == selected_group).first()
            existing_request = db.query(GroupRequest).filter(
                GroupRequest.user_id == user_id,
                GroupRequest.group_id == group.id,
                GroupRequest.status == "Pending"
            ).first()
            if existing_request:
                st.warning(f"⚠️ You have already requested to join '{selected_group}'. Please wait for approval.")
            else:
                new_request = GroupRequest(user_id=user_id, group_id=group.id)
                db.add(new_request)
                db.commit()
                db.close()
                st.success(f"✅ Request to join group '{selected_group}' submitted.")
    else:
        st.info("📁 No available groups to join or you are already a member of all groups.")


# === Main Application Logic ===
def main():
    """Main function to control the flow of the Streamlit application."""
    if not st.session_state['authentication_status']:
        login()
    else:
        user_id = st.session_state['user_id']
        username = st.session_state['username']
        is_admin = st.session_state['is_admin']
        dark_mode = st.session_state.get('dark_mode', False)

        # Ensure CSS is applied based on user preference
        inject_css(dark_mode=dark_mode)

        # Navigation Sidebar with Icons and Tooltips
        nav_options = ["📤 Upload Files", "📥 Download Files", "👥 Your Groups", "⚙️ User Settings"]
        if is_admin:
            nav_options += ["🛠️ Admin Panel"]
        nav = st.sidebar.radio(
            "Navigation",
            nav_options,
            help="Navigate through the application."
        )

        # Render content based on navigation selection
        if nav == "📤 Upload Files":
            upload_interface(user_id, username)
        elif nav == "📥 Download Files":
            download_interface(user_id)
        elif nav == "👥 Your Groups":
            user_groups_interface(user_id)
        elif nav == "⚙️ User Settings":
            user_settings_interface(user_id)
        elif nav == "🛠️ Admin Panel" and is_admin:
            admin_interface()

        # Logout Button at the Bottom of Sidebar
        st.sidebar.markdown("---")
        if st.sidebar.button("🔓 Logout", type="secondary"):
            logout()


# Execute the main function when the script is run
if __name__ == "__main__":
    main()