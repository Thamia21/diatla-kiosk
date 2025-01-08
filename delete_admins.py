from app import app, db
from models import User

def delete_admins():
    with app.app_context():
        # Get all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        # Print current admins
        print("Current admin users:")
        for admin in admin_users:
            print(f"- {admin.email}")
        
        # Delete all admin users
        count = User.query.filter_by(is_admin=True).delete()
        
        # Commit the changes
        db.session.commit()
        
        print(f"\nDeleted {count} admin users from the database.")

if __name__ == '__main__':
    delete_admins()
