from app import app, db
from models import Category, MenuItem
import json

def restore_menu():
    with app.app_context():
        print("Loading menu data...")
        with open('menu_data.json', 'r') as f:
            menu_data = json.load(f)
        
        print("Clearing existing menu data...")
        MenuItem.query.delete()
        Category.query.delete()
        db.session.commit()
        
        print("Creating categories...")
        category_objects = {}
        
        # Category display names and icons
        category_info = {
            'burgers': {'display_name': 'Burgers', 'icon': 'burger'},
            'chicken': {'display_name': 'Chicken', 'icon': 'chicken'},
            'grills': {'display_name': 'Grills', 'icon': 'grill'},
            'african_cuisine': {'display_name': 'African Cuisine', 'icon': 'african'},
            'combos': {'display_name': 'Combos', 'icon': 'combo'},
            'salads': {'display_name': 'Salads', 'icon': 'salad'},
            'milkshakes': {'display_name': 'Milkshakes', 'icon': 'milkshake'},
            'hot_drinks': {'display_name': 'Hot Drinks', 'icon': 'hot-drink'},
            'beverages': {'display_name': 'Beverages', 'icon': 'beverage'},
            'desserts': {'display_name': 'Desserts', 'icon': 'dessert'}
        }
        
        # Create categories
        for category_name in menu_data.keys():
            info = category_info[category_name]
            category = Category(
                name=category_name,
                display_name=info['display_name'],
                icon=info['icon']
            )
            db.session.add(category)
            category_objects[category_name] = category
        
        db.session.commit()
        print("Categories created!")
        
        print("Creating menu items...")
        # Add menu items
        for category_name, items in menu_data.items():
            category = category_objects[category_name]
            for item_data in items:
                menu_item = MenuItem(
                    name=item_data['name'],
                    description=item_data.get('description', ''),
                    price=item_data['price'],
                    image_url=item_data['image_url'],
                    category_id=category.id,
                    available=True
                )
                db.session.add(menu_item)
        
        db.session.commit()
        print("Menu items created!")
        print("Menu restoration complete!")

if __name__ == '__main__':
    restore_menu()
