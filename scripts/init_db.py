# scripts/init_db.py

from sharesphere.database import engine, Base
from sharesphere.models import User, Group, File, FileSharing, GroupRequest

def init_db():
    # Drop all tables in the database
    Base.metadata.drop_all(bind=engine)
    print("Dropped all tables successfully.")
    
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
