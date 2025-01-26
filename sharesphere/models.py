# sharesphere/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# Association table for the many-to-many relationship between User and Group
user_group_association = Table(
    'user_group_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('groups.id'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    dark_mode_pref = Column(Boolean, default=False)  # Add dark_mode_pref attribute
    
    files = relationship("File", back_populates="owner")
    shared_files = relationship("FileSharing", back_populates="user")
    groups = relationship("Group", secondary=user_group_association, back_populates="members")
    group_requests = relationship("GroupRequest", back_populates="user")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    members = relationship("User", secondary=user_group_association, back_populates="groups")
    group_requests = relationship("GroupRequest", back_populates="group")

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    comment = Column(String, nullable=True)  # Add comment field
    
    owner = relationship("User", back_populates="files")
    shared_with = relationship("FileSharing", back_populates="file")

class FileSharing(Base):
    __tablename__ = "file_sharing"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_shared = Column(Boolean, default=False)  # True means shared with the user
    
    file = relationship("File", back_populates="shared_with")
    user = relationship("User", back_populates="shared_files")

class GroupRequest(Base):
    __tablename__ = "group_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="group_requests")
    group = relationship("Group", back_populates="group_requests")