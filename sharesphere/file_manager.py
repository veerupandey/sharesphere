# sharesphere/file_manager.py

from .database import SessionLocal
from .models import File, FileSharing, Group
from sharesphere.models import User
from sqlalchemy.orm import joinedload  # Ensure this import is correct
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

def upload_file(uploader_id: int, uploader_name: str, file_storage, file_comment: str, shared_with_group: bool, shared_users: list, shared_groups: list):
    filename = file_storage.name
    upload_folder = Path("uploads") / uploader_name
    upload_folder.mkdir(parents=True, exist_ok=True)
    file_path = upload_folder / filename
    
    try:
        with open(file_path, "wb") as f:
            f.write(file_storage.getbuffer())
        logger.info(f"File '{filename}' uploaded by user ID {uploader_id} to '{uploader_name}' folder.")
        
        # Add file record to the database
        db = SessionLocal()
        new_file = File(filename=filename, filepath=str(file_path), owner_id=uploader_id, comment=file_comment)
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        
        # Handle sharing permissions
        if shared_with_group:
            users = db.query(User).all()
            for user in users:
                if user.id != uploader_id:
                    fs = FileSharing(file_id=new_file.id, user_id=user.id, is_shared=True)
                    db.add(fs)
            db.commit()
            logger.info(f"File '{filename}' shared with the entire group by user ID {uploader_id}.")
        elif shared_users:
            for user_id in shared_users:
                fs = FileSharing(file_id=new_file.id, user_id=user_id, is_shared=True)
                db.add(fs)
            db.commit()
            logger.info(f"File '{filename}' shared with specific users by user ID {uploader_id}.")
        elif shared_groups:
            for group_id in shared_groups:
                group = db.query(Group).filter(Group.id == group_id).first()
                for user in group.members:
                    if user.id != uploader_id:
                        fs = FileSharing(file_id=new_file.id, user_id=user.id, is_shared=True)
                        db.add(fs)
            db.commit()
            logger.info(f"File '{filename}' shared with specific groups by user ID {uploader_id}.")
        else:
            logger.info(f"File '{filename}' uploaded without sharing by user ID {uploader_id}.")
        
        db.close()
        return True, "File uploaded successfully."
    except Exception as e:
        logger.error(f"Error uploading file '{filename}': {e}")
        return False, "Failed to upload file."

def get_shared_files(user_id: int):
    db = SessionLocal()
    # Files owned by the user
    own_files = db.query(File).options(joinedload(File.owner)).filter(File.owner_id == user_id).all()
    # Files shared with the user
    shared_file_links = db.query(File).options(joinedload(File.owner)).join(FileSharing).filter(FileSharing.user_id == user_id, FileSharing.is_shared == True).all()
    db.close()
    return own_files, shared_file_links

def delete_file(file_id: int, user_id: int, admin: bool = False):
    db = SessionLocal()
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        db.close()
        logger.warning(f"File ID '{file_id}' not found.")
        return False, "File not found."
    
    if not admin and file.owner_id != user_id:
        db.close()
        logger.warning(f"User ID '{user_id}' attempted to delete file ID '{file_id}' without permission.")
        return False, "You do not have permission to delete this file."
    
    try:
        os.remove(file.filepath)
        db.delete(file)
        # Also delete sharing records
        db.query(FileSharing).filter(FileSharing.file_id == file_id).delete()
        db.commit()
        logger.info(f"File '{file.filename}' deleted by user ID '{user_id}'.")
        db.close()
        return True, "File deleted successfully."
    except Exception as e:
        logger.error(f"Error deleting file ID '{file_id}': {e}")
        db.close()
        return False, "Failed to delete file."