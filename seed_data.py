from app import app, db
from models import Category, MenuItem

def seed_data():
    with app.app_context():
        print("Creating categories...")
        
        # Create categories
        categories = [
            {
                'name': 'burgers',
                'display_name': 'Burgers',
                'icon': 'burger'
            },
            {
                'name': 'chicken',
                'display_name': 'Chicken',
                'icon': 'chicken'
            },
            {
                'name': 'grills',
                'display_name': 'Grills',
                'icon': 'grill'
            },
            {
                'name': 'african_cuisine',
                'display_name': 'African Cuisine',
                'icon': 'african'
            },
            {
                'name': 'combos',
                'display_name': 'Combos',
                'icon': 'combo'
            },
            {
                'name': 'salads',
                'display_name': 'Salads',
                'icon': 'salad'
            },
            {
                'name': 'milkshakes',
                'display_name': 'Milkshakes',
                'icon': 'milkshake'
            },
            {
                'name': 'hot_drinks',
                'display_name': 'Hot Drinks',
                'icon': 'hot-drink'
            },
            {
                'name': 'beverages',
                'display_name': 'Beverages',
                'icon': 'beverage'
            },
            {
                'name': 'desserts',
                'display_name': 'Desserts',
                'icon': 'dessert'
            }
        ]
        
        category_objects = {}
        for cat_data in categories:
            category = Category(
                name=cat_data['name'],
                display_name=cat_data['display_name'],
                icon=cat_data['icon']
            )
            db.session.add(category)
            category_objects[cat_data['name']] = category
        
        db.session.commit()
        print("Categories created!")
        
        print("Creating menu items...")
        
        # Menu items for each category
        menu_items = {
            'burgers': [
                {
                    'name': 'Classic Beef Burger',
                    'description': 'Juicy beef patty with lettuce, tomato, and our special sauce',
                    'price': 89.99,
                    'image_url': '/static/images/menu/classic-burger.jpg'
                },
                {
                    'name': 'Cheese Burger',
                    'description': 'Classic beef burger with melted cheddar cheese',
                    'price': 99.99,
                    'image_url': '/static/images/menu/cheese-burger.jpg'
                }
            ],
            'chicken': [
                {
                    'name': 'Grilled Chicken',
                    'description': 'Marinated chicken breast, grilled to perfection',
                    'price': 79.99,
                    'image_url': '/static/images/menu/grilled-chicken.jpg'
                },
                {
                    'name': 'Chicken Wings',
                    'description': '8 pieces of crispy wings with your choice of sauce',
                    'price': 89.99,
                    'image_url': '/static/images/menu/chicken-wings.jpg'
                }
            ],
            'grills': [
                {
                    'name': 'T-Bone Steak',
                    'description': '300g T-bone steak grilled to your preference',
                    'price': 189.99,
                    'image_url': '/static/images/menu/tbone-steak.jpg'
                },
                {
                    'name': 'Lamb Chops',
                    'description': '4 pieces of tender lamb chops with mint sauce',
                    'price': 199.99,
                    'image_url': '/static/images/menu/lamb-chops.jpg'
                }
            ],
            'african_cuisine': [
                {
                    'name': 'Pap and Wors',
                    'description': 'Traditional pap served with grilled boerewors',
                    'price': 89.99,
                    'image_url': '/static/images/menu/pap-wors.jpg'
                },
                {
                    'name': 'Mogodu',
                    'description': 'Traditional tripe served with pap or samp',
                    'price': 99.99,
                    'image_url': '/static/images/menu/mogodu.jpg'
                }
            ],
            'combos': [
                {
                    'name': 'Family Feast',
                    'description': '2 burgers, 1 large chips, 4 wings, and 2 drinks',
                    'price': 299.99,
                    'image_url': '/static/images/menu/family-feast.jpg'
                },
                {
                    'name': 'Date Night',
                    'description': '2 steaks, 2 sides, and 2 glasses of wine',
                    'price': 399.99,
                    'image_url': '/static/images/menu/date-night.jpg'
                }
            ],
            'salads': [
                {
                    'name': 'Greek Salad',
                    'description': 'Fresh lettuce, olives, feta, and Mediterranean dressing',
                    'price': 69.99,
                    'image_url': '/static/images/menu/greek-salad.jpg'
                },
                {
                    'name': 'Chicken Caesar',
                    'description': 'Grilled chicken breast on classic Caesar salad',
                    'price': 89.99,
                    'image_url': '/static/images/menu/caesar-salad.jpg'
                }
            ],
            'milkshakes': [
                {
                    'name': 'Vanilla Shake',
                    'description': 'Classic vanilla milkshake with whipped cream',
                    'price': 39.99,
                    'image_url': '/static/images/menu/vanilla-shake.jpg'
                },
                {
                    'name': 'Chocolate Shake',
                    'description': 'Rich chocolate milkshake with chocolate sauce',
                    'price': 39.99,
                    'image_url': '/static/images/menu/chocolate-shake.jpg'
                }
            ],
            'hot_drinks': [
                {
                    'name': 'Cappuccino',
                    'description': 'Espresso topped with foamy milk',
                    'price': 29.99,
                    'image_url': '/static/images/menu/cappuccino.jpg'
                },
                {
                    'name': 'Hot Chocolate',
                    'description': 'Rich and creamy hot chocolate with marshmallows',
                    'price': 34.99,
                    'image_url': '/static/images/menu/hot-chocolate.jpg'
                }
            ],
            'beverages': [
                {
                    'name': 'Soft Drinks',
                    'description': 'Various 330ml soft drinks',
                    'price': 19.99,
                    'image_url': '/static/images/menu/soft-drinks.jpg'
                },
                {
                    'name': 'Fresh Juice',
                    'description': 'Orange, apple, or mixed fruit juice',
                    'price': 29.99,
                    'image_url': '/static/images/menu/fresh-juice.jpg'
                }
            ],
            'desserts': [
                {
                    'name': 'Malva Pudding',
                    'description': 'Traditional South African dessert with custard',
                    'price': 49.99,
                    'image_url': '/static/images/menu/malva-pudding.jpg'
                },
                {
                    'name': 'Ice Cream',
                    'description': '3 scoops of vanilla ice cream with chocolate sauce',
                    'price': 39.99,
                    'image_url': '/static/images/menu/ice-cream.jpg'
                }
            ]
        }
        
        # Add menu items
        for category_name, items in menu_items.items():
            category = category_objects[category_name]
            for item_data in items:
                menu_item = MenuItem(
                    name=item_data['name'],
                    description=item_data['description'],
                    price=item_data['price'],
                    image_url=item_data['image_url'],
                    category_id=category.id
                )
                db.session.add(menu_item)
        
        db.session.commit()
        print("Menu items created!")

if __name__ == '__main__':
    seed_data()
