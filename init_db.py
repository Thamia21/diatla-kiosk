from app import app, db
from models import Category, MenuItem, User, Order, OrderItem, Settings
import json
from datetime import datetime

def init_db():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all database tables...")
        db.create_all()
        
        print("Creating admin user...")
        # Create admin user
        admin = User(
            username='admin',
            email='admin@diatla.com',
            is_admin=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()
        
        print("Creating categories...")
        # Create categories with exact names matching menu_data.json
        categories = [
            {'name': 'burgers', 'display_name': 'Burgers', 'icon': 'bx-food-menu'},
            {'name': 'chicken', 'display_name': 'Chicken', 'icon': 'bx-bowl-hot'},
            {'name': 'grills', 'display_name': 'Grills', 'icon': 'bx-restaurant'},
            {'name': 'african_cuisine', 'display_name': 'African Cuisine', 'icon': 'bx-dish'},
            {'name': 'combos', 'display_name': 'Combos', 'icon': 'bx-package'},
            {'name': 'salads', 'display_name': 'Salads', 'icon': 'bx-salad'},
            {'name': 'milkshakes', 'display_name': 'Milkshakes', 'icon': 'bx-drink'},
            {'name': 'hot_drinks', 'display_name': 'Hot Drinks', 'icon': 'bx-coffee'},
            {'name': 'beverages', 'display_name': 'Beverages', 'icon': 'bx-drink'},
            {'name': 'desserts', 'display_name': 'Desserts', 'icon': 'bx-cookie'}
        ]
        
        for cat_data in categories:
            category = Category(**cat_data)
            db.session.add(category)
        db.session.commit()
        
        print("Creating menu items...")
        # Load menu items from JSON file
        try:
            with open('menu_data.json', 'r') as f:
                menu_data = json.load(f)
                
            for category_name, items in menu_data.items():
                category = Category.query.filter_by(name=category_name).first()
                if category:
                    for item_data in items:
                        menu_item = MenuItem(
                            name=item_data['name'],
                            description=item_data.get('description', ''),
                            price=float(item_data['price']),
                            image_url=item_data.get('image_url', ''),
                            category_id=category.id,
                            available=True
                        )
                        db.session.add(menu_item)
            db.session.commit()
            print("Menu items created successfully!")
            
        except FileNotFoundError:
            print("Warning: menu_data.json not found. Skipping menu item creation.")
            pass
        except Exception as e:
            print(f"Error creating menu items: {str(e)}")
            pass

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialization complete!")
