# sharesphere/admin.py

from .database import SessionLocal
from .models import User, File, FileSharing, Group, GroupRequest
from .auth import create_user, get_user_by_username, update_user_password
import logging
import os

logger = logging.getLogger(__name__)

def list_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users

def create_new_user(username: str, password: str, is_admin: bool = False, group_names: list = []):
    user = create_user(username, password, is_admin)
    if user:
        db = SessionLocal()
        for group_name in group_names:
            group = db.query(Group).filter(Group.name == group_name).first()
            if group:
                group.members.append(user)
        db.commit()
        db.close()
        logger.info(f"Admin created user '{username}' and assigned to groups: {group_names}.")
    return user

def delete_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        logger.warning(f"Admin attempted to delete nonexistent user ID '{user_id}'.")
        return False, "User not found."
    try:
        # Delete user files
        user_folder = os.path.join("uploads", user.username)
        if os.path.exists(user_folder):
            for file in os.listdir(user_folder):
                file_path = os.path.join(user_folder, file)
                os.remove(file_path)
            os.rmdir(user_folder)
        
        # Delete user from database
        db.delete(user)
        # Also delete shared files
        db.query(FileSharing).filter(FileSharing.user_id == user_id).delete()
        db.commit()
        logger.info(f"Admin deleted user '{user.username}' and their data.")
        db.close()
        return True, "User deleted successfully."
    except Exception as e:
        logger.error(f"Error deleting user ID '{user_id}': {e}")
        db.close()
        return False, "Failed to delete user."

def reset_user_password(user_id: int, new_password: str):
    success = update_user_password(user_id, new_password)
    if success:
        logger.info(f"Admin reset password for user ID '{user_id}'.")
        return True, "Password reset successfully."
    else:
        logger.error(f"Admin failed to reset password for user ID '{user_id}'.")
        return False, "Failed to reset password."

def get_system_logs():
    log_file = os.path.join("logs", "app.log")
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = f.readlines()
        return ''.join(logs[-100:])  # Return last 100 log entries
    else:
        return "No logs available."

def list_groups():
    db = SessionLocal()
    groups = db.query(Group).all()
    db.close()
    return groups

def create_new_group(name: str):
    db = SessionLocal()
    group = db.query(Group).filter(Group.name == name).first()
    if group:
        db.close()
        return None
    new_group = Group(name=name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    db.close()
    return new_group

def list_group_requests():
    db = SessionLocal()
    requests = db.query(GroupRequest).all()
    db.close()
    return requests

def approve_group_request(request_id: int):
    db = SessionLocal()
    request = db.query(GroupRequest).filter(GroupRequest.id == request_id).first()
    if request:
        request.status = "approved"
        group = db.query(Group).filter(Group.id == request.group_id).first()
        user = db.query(User).filter(User.id == request.user_id).first()
        group.members.append(user)
        db.commit()
        db.close()
        return True, "Group request approved."
    db.close()
    return False, "Group request not found."

def reject_group_request(request_id: int):
    db = SessionLocal()
    request = db.query(GroupRequest).filter(GroupRequest.id == request_id).first()
    if request:
        request.status = "rejected"
        db.commit()
        db.close()
        return True, "Group request rejected."
    db.close()
    return False, "Group request not found."