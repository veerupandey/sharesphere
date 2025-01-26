# sharesphere/auth.py

from .database import SessionLocal
from .models import User
import bcrypt
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

def get_user_by_username(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    return user

def create_user(username: str, password: str, is_admin: bool = False):
    db = SessionLocal()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=username, hashed_password=hashed_pw, is_admin=is_admin)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User '{username}' created successfully.")
        return user
    except IntegrityError:
        db.rollback()
        logger.warning(f"Attempt to create duplicate user '{username}'.")
        return None
    finally:
        db.close()

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        logger.warning(f"Authentication failed for nonexistent user '{username}'.")
        return False, False  # (IsAuthenticated, IsAdmin)
    is_correct = bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8'))
    if is_correct:
        logger.info(f"User '{username}' authenticated successfully.")
        return True, user.is_admin
    else:
        logger.warning(f"Authentication failed for user '{username}'. Incorrect password.")
        return False, False

def update_user_password(user_id: int, new_password: str):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.hashed_password = hashed_pw
        db.commit()
        logger.info(f"Password for user '{user.username}' updated successfully.")
        db.close()
        return True
    else:
        db.close()
        logger.error(f"Attempted to update password for nonexistent user ID '{user_id}'.")
        return False