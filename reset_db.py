import os
from app import app, db
from models import *

def reset_database():
    # Delete the database file if it exists
    db_path = 'diatla.db'
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Deleted existing database file: {db_path}")
        except Exception as e:
            print(f"Error deleting database file: {e}")
    
    # Create new database
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Database reset complete!")

if __name__ == '__main__':
    reset_database()
