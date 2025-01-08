from app import app, db
from models import User

def create_admin():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@diatla.com').first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@diatla.com',
            is_admin=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
        print("Email: admin@diatla.com")
        print("Password: Admin123!")

if __name__ == '__main__':
    create_admin()
