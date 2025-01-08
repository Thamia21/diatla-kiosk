from app import app, db
from models import Order

with app.app_context():
    orders = Order.query.all()
    print('Orders:', [(o.order_number, o.status, o.total_amount) for o in orders])
