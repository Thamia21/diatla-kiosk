from app import app, db
from models import Order, OrderItem, MenuItem
from datetime import datetime
import pytz

def get_next_order_number():
    last_order = Order.query.order_by(Order.id.desc()).first()
    if last_order:
        try:
            last_num = int(last_order.order_number)
            next_num = str(last_num + 1).zfill(4)
        except ValueError:
            next_num = '0001'
    else:
        next_num = '0001'
    return next_num

def create_test_order():
    with app.app_context():
        # Get a menu item for the test order
        menu_item = MenuItem.query.first()
        if not menu_item:
            print("No menu items found!")
            return
        
        # Get next order number
        order_number = get_next_order_number()
        
        # Create a test order
        order = Order(
            order_number=order_number,
            customer_name='Test Customer',
            customer_email='test@example.com',
            customer_phone='1234567890',
            total_amount=menu_item.price,
            status='paid',
            payment_method='card',  
            created_at=datetime.now(pytz.timezone('Africa/Johannesburg'))
        )
        db.session.add(order)
        db.session.commit()
        
        # Add order item
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            quantity=1,
            price=menu_item.price
        )
        db.session.add(order_item)
        db.session.commit()
        
        print(f"Test order created with order number: {order.order_number}")

if __name__ == '__main__':
    create_test_order()
