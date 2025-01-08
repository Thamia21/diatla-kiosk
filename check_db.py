from app import app, db, Order, OrderItem, MenuItem

def check_database():
    print("\n=== Checking Database ===")
    
    # Check Orders
    print("\nAll Orders:")
    orders = Order.query.all()
    print(f"Total orders found: {len(orders)}")
    
    for order in orders:
        print(f"\nOrder #{order.id}")
        print(f"Customer: {order.customer_name}")
        print(f"Email: {order.customer_email}")
        print(f"Total: R{order.total_amount}")
        print(f"Status: {order.status}")
        print(f"Created: {order.created_at}")
        
        # Get order items
        items = OrderItem.query.filter_by(order_id=order.id).all()
        print("Items:")
        for item in items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                print(f"- {menu_item.name} x{item.quantity} @ R{item.price} each")
            else:
                print(f"- Unknown item (ID: {item.menu_item_id}) x{item.quantity}")

if __name__ == '__main__':
    with app.app_context():
        check_database()
