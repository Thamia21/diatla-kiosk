from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from models import db, User, MenuItem, Category, Order, OrderItem, Settings
from auth import admin_required, login_manager
import stripe
from utils.email import EmailSender
from functools import wraps
from flask import session, request
import qrcode
import io
import base64
from datetime import timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_migrate import Migrate
import secrets
import random
from flask_mail import Message, Mail
import time
import requests
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diatla.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51QblhaFsOUQ1Ki6SYSLGrsjZVmW5NHMEk7qUWjFwttOyVl3bLVXckx2zBoGYuazcL2iDmKvbHQ3hF24a6xSRxF1f00dAwtVrOn'
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51QblhaFsOUQ1Ki6Sno6uBtmR8rSu4VpcWCA37KeahS7QnauIGtHSxrSZrnEsUcn0Svb5V7y0TixwN0bqRuifp3UX00LoqNTGL3'

# Add permanent session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Set session lifetime to 1 day
app.config['SESSION_PERMANENT'] = True

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "thamiakeneilwe1@gmail.com"
app.config['MAIL_PASSWORD'] = "your-app-password-here"  # You'll need to replace this with an App Password
app.config['MAIL_DEFAULT_SENDER'] = "thamiakeneilwe1@gmail.com"
app.config['ADMIN_EMAIL'] = "thamiakeneilwe1@gmail.com"

# Upload folder configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize Mail
mail = Mail()
mail.init_app(app)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)

# Initialize email sender
email_sender = EmailSender(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Security middleware
def check_password_expiry():
    if current_user.is_authenticated:
        if current_user.password_expires_at and datetime.utcnow() > current_user.password_expires_at:
            flash('Your password has expired. Please change it to continue.', 'warning')
            return redirect(url_for('change_password'))

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.check_rate_limit():
            flash('Too many requests. Please try again later.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def require_2fa(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.two_factor_enabled:
            if not session.get('2fa_verified'):
                return redirect(url_for('verify_2fa'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    if current_user.is_authenticated:
        # Check session expiry
        if 'session_expires' in session:
            if datetime.utcnow() > datetime.fromtimestamp(session['session_expires']):
                logout_user()
                flash('Your session has expired. Please login again.', 'info')
                return redirect(url_for('admin_login'))
        
        # Refresh session expiry
        session['session_expires'] = (datetime.utcnow() + timedelta(hours=24)).timestamp()

# Admin Authentication Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if account is locked
            if user.account_locked:
                flash('Your account is locked. Please contact support.', 'danger')
                return redirect(url_for('admin_login'))
            
            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            db.session.commit()
            
            # Log the user in and set session expiry
            login_user(user, remember=remember)
            session.permanent = True
            session['_user_id'] = user.id
            session['session_expires'] = (datetime.utcnow() + timedelta(days=1)).timestamp()
            
            # Check if 2FA is required
            if user.two_factor_enabled:
                return redirect(url_for('verify_2fa'))
                
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            # Handle failed login attempt
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:  # Lock account after 5 failed attempts
                    user.account_locked = True
                    flash('Account locked due to too many failed attempts. Please contact support.', 'danger')
                else:
                    flash('Invalid password. Please try again.', 'danger')
                db.session.commit()
            else:
                flash('Invalid email address. Please try again.', 'danger')
            
        return redirect(url_for('admin_login'))
    
    return render_template('admin/login.html')

@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        admin_code = request.form.get('admin_code')
        
        # Basic validation
        if not email or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin_signup'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin_signup'))
            
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('admin_signup'))
        
        # Check if this is the first admin
        existing_admin = User.query.filter_by(is_admin=True).first()
        
        # If not first admin, require admin code
        if existing_admin:
            if not admin_code or admin_code != 'DIATLA2024':  # You should change this to a secure code
                flash('Invalid admin code.', 'danger')
                return redirect(url_for('admin_signup'))
            
        # Create new user
        user = User(
            email=email,
            username=email.split('@')[0],  # Use part before @ as username
            email_verified=False,  # Don't auto-verify email
            is_admin=True if not existing_admin else False,  # Only first user is auto-admin
            failed_login_attempts=0,
            account_locked=False
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            if not existing_admin:
                flash('First admin account created successfully! You can now log in.', 'success')
            else:
                flash('Account created successfully! Please wait for an existing admin to approve your account.', 'success')
            return redirect(url_for('admin_login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('admin_signup'))
            
    return render_template('admin/signup.html')

@app.route('/admin/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    
    if user:
        if not user.email_verified:
            user.email_verified = True
            user.verification_token = None
            db.session.commit()
            flash('Email verified successfully! You can now login.', 'success')
        else:
            flash('Email already verified. Please login.', 'info')
    else:
        flash('Invalid or expired verification link.', 'danger')
    
    return redirect(url_for('admin_login'))

@app.route('/admin/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            reset_token = user.generate_reset_token()
            db.session.commit()
            
            if email_sender.send_reset_password_email(user):
                flash('Password reset instructions have been sent to your email.', 'success')
            else:
                flash('Failed to send reset email. Please try again later.', 'danger')
        else:
            # For security, don't reveal if email exists
            flash('If an account exists with this email, you will receive password reset instructions.', 'info')
        
        return redirect(url_for('admin_login'))
    
    return render_template('admin/forgot_password.html')

@app.route('/admin/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('admin/reset_password.html')
        
        try:
            user.set_password(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            
            flash('Password reset successful! You can now login with your new password.', 'success')
            return redirect(url_for('admin_login'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('admin/reset_password.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    # Clear session data
    session.clear()
    # Clear remember token
    if current_user.is_authenticated:
        current_user.remember_token = None
        db.session.commit()
    # Logout user
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

# Admin Dashboard Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin dashboard.', 'error')
        return redirect(url_for('home'))
    return render_template('admin/dashboard.html')

@app.route('/api/admin/recent-orders')
@login_required
def get_recent_orders():
    try:
        app.logger.info("Getting recent orders...")
        
        # Get orders with eager loading of relationships
        orders = Order.query.options(
            db.joinedload(Order.items).joinedload(OrderItem.menu_item)
        ).order_by(Order.created_at.desc()).limit(10).all()
        
        app.logger.info(f"Found {len(orders)} orders")
        
        # Convert to local timezone
        local_tz = pytz.timezone('Africa/Johannesburg')
        
        orders_list = []
        for order in orders:
            # Process order items with proper error handling
            items_text = []
            try:
                for order_item in order.items:
                    menu_item = order_item.menu_item
                    if menu_item:
                        items_text.append(f"{menu_item.name} x{order_item.quantity}")
                    else:
                        app.logger.warning(f"Menu item not found for order item {order_item.id}")
            except Exception as e:
                app.logger.error(f"Error processing items for order {order.id}: {str(e)}")
                items_text = ['Error loading items']
            
            # Convert UTC time to local time
            local_time = order.created_at.replace(tzinfo=pytz.UTC).astimezone(local_tz)
            
            order_data = {
                'id': order.id,
                'order_number': f"{int(order.order_number):04d}",
                'customer': order.customer_name,
                'items': ', '.join(items_text) if items_text else 'No items',
                'total': float(order.total_amount),
                'status': order.status,
                'created_at': local_time.isoformat()
            }
            
            app.logger.info(f"Processed order data: {order_data}")
            orders_list.append(order_data)
        
        app.logger.info(f"Returning {len(orders_list)} orders")
        return jsonify(orders_list)
        
    except Exception as e:
        app.logger.error(f"Error getting recent orders: {str(e)}")
        app.logger.exception(e)  # Log full stack trace
        return jsonify([])

@app.route('/api/admin/orders')
@login_required
def get_all_orders():
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        date = request.args.get('date', '')
        search = request.args.get('search', '')
        
        # Start with base query
        query = Order.query
        
        # Apply status filter
        if status != 'all':
            query = query.filter(Order.status == status)
            
        # Apply date filter
        if date:
            try:
                filter_date = datetime.strptime(date, '%Y-%m-%d').date()
                day_start = datetime.combine(filter_date, time.min)
                day_end = datetime.combine(filter_date, time.max)
                query = query.filter(Order.created_at.between(day_start, day_end))
            except ValueError:
                pass  # Invalid date format, ignore filter
                
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Order.order_number.ilike(search_term),
                    Order.customer_name.ilike(search_term),
                    Order.customer_email.ilike(search_term)
                )
            )
            
        # Get orders ordered by creation date (newest first)
        orders = query.order_by(Order.created_at.desc()).all()
        
        orders_list = []
        for order in orders:
            # Get items for this order
            items = OrderItem.query.filter_by(order_id=order.id).all()
            items_list = []
            for item in items:
                menu_item = MenuItem.query.get(item.menu_item_id)
                if menu_item:
                    items_list.append({
                        'name': menu_item.name,
                        'quantity': item.quantity
                    })
            
            orders_list.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer': order.customer_name,
                'items': items_list,
                'total': float(order.total_amount),
                'status': order.status,
                'created_at': order.created_at.isoformat()
            })
        
        return jsonify(orders_list)
        
    except Exception as e:
        app.logger.error(f"Error getting all orders: {str(e)}")
        return jsonify([])

@app.route('/api/admin/dashboard')
@login_required
@admin_required
def get_dashboard_data():
    try:
        # Get today's date range (from midnight to midnight)
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Get today's orders with completed or paid status
        today_orders = Order.query.filter(
            Order.created_at.between(today_start, today_end),
            Order.status.in_(['completed', 'paid'])
        ).all()
        
        # Calculate today's revenue from order items
        today_revenue = 0
        for order in today_orders:
            if order.total_amount:
                try:
                    today_revenue += float(order.total_amount)
                except (ValueError, TypeError):
                    app.logger.error(f"Invalid total_amount for order {order.id}: {order.total_amount}")
                    continue
        
        # Get total menu items and categories
        total_items = MenuItem.query.count()
        total_categories = Category.query.count()
        
        return jsonify({
            'todayOrders': len(today_orders),
            'todayRevenue': today_revenue,
            'totalItems': total_items,
            'totalCategories': total_categories
        })
        
    except Exception as e:
        app.logger.error(f"Error in get_dashboard_data: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@app.route('/api/place_order', methods=['POST'])
def api_place_order():
    try:
        data = request.json
        
        # Generate a 4-digit order number
        last_order = Order.query.order_by(Order.id.desc()).first()
        if last_order:
            last_number = int(last_order.order_number)
            new_number = (last_number + 1) % 10000  # Keep it 4 digits
        else:
            new_number = 1
            
        # Pad with zeros to maintain 4 digits
        order_number = f"{new_number:04d}"
        
        # Create new order with all required fields
        order = Order(
            order_number=order_number,
            customer_name=data['customerName'],
            customer_email=data.get('customerEmail', ''),
            customer_phone=data.get('customerPhone', ''),
            special_instructions=data.get('specialInstructions', ''),
            payment_method=data['paymentMethod'],
            total_amount=data['totalAmount'],
            status='pending',
            created_at=datetime.now()
        )
        
        # Get all menu items at once
        menu_items = {item.name: item for item in MenuItem.query.filter(
            MenuItem.name.in_([item['name'] for item in data['items']])
        ).all()}
        
        # Create order items
        order_items = []
        for item in data['items']:
            menu_item = menu_items.get(item['name'])
            if menu_item:
                order_item = OrderItem(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    price=menu_item.price
                )
                order_items.append(order_item)
        
        # Add all objects to session
        db.session.add(order)
        db.session.add_all(order_items)
        
        # Commit transaction
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'order_number': order_number
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error placing order: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/menu-items', methods=['GET', 'POST'])
@app.route('/api/admin/menu-items/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@admin_required
def handle_menu_items(item_id=None):
    if request.method == 'GET':
        if item_id:
            # Get specific menu item
            item = MenuItem.query.get_or_404(item_id)
            return jsonify({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'category': {
                    'id': item.category.id,
                    'name': item.category.name
                },
                'price': float(item.price),
                'image_url': item.image_url,
                'available': item.available
            })
        else:
            # Get all menu items
            items = MenuItem.query.all()
            return jsonify([{
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'category': {
                    'id': item.category.id,
                    'name': item.category.name
                },
                'price': float(item.price),
                'image_url': item.image_url,
                'available': item.available
            } for item in items])
            
    elif request.method == 'POST':
        try:
            # Create new menu item
            name = request.form.get('name')
            category_id = request.form.get('category')
            price = request.form.get('price')
            description = request.form.get('description', '')
            available = request.form.get('available', 'true').lower() == 'true'
            
            if not all([name, category_id, price]):
                return jsonify({'error': 'Missing required fields'}), 400
                
            # Handle image source (file upload or URL)
            image_url = None
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_url = f'/static/uploads/{filename}'
            elif 'image_url' in request.form:
                image_url = request.form.get('image_url')
            
            # Create menu item
            menu_item = MenuItem(
                name=name,
                description=description,
                category_id=category_id,
                price=float(price),
                image_url=image_url,
                available=available
            )
            
            db.session.add(menu_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Menu item created successfully',
                'item': {
                    'id': menu_item.id,
                    'name': menu_item.name,
                    'description': menu_item.description,
                    'category': {
                        'id': menu_item.category.id,
                        'name': menu_item.category.name
                    },
                    'price': float(menu_item.price),
                    'image_url': menu_item.image_url,
                    'available': menu_item.available
                }
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating menu item: {str(e)}")
            return jsonify({'error': 'Failed to create menu item'}), 500
            
    elif request.method == 'PUT':
        try:
            # Update menu item
            item = MenuItem.query.get_or_404(item_id)
            
            item.name = request.form.get('name', item.name)
            item.category_id = request.form.get('category', item.category_id)
            item.price = float(request.form.get('price', item.price))
            item.description = request.form.get('description', item.description)
            item.available = request.form.get('available', str(item.available)).lower() == 'true'
            
            # Handle image update
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    # Delete old image if it exists and is a local file
                    if item.image_url and item.image_url.startswith('/static/uploads/'):
                        old_filepath = os.path.join(app.root_path, item.image_url.lstrip('/'))
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                    
                    # Save new image
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    item.image_url = f'/static/uploads/{filename}'
            elif 'image_url' in request.form:
                # Update image URL
                new_url = request.form.get('image_url')
                if new_url != item.image_url:
                    # Delete old image if it exists and is a local file
                    if item.image_url and item.image_url.startswith('/static/uploads/'):
                        old_filepath = os.path.join(app.root_path, item.image_url.lstrip('/'))
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                    item.image_url = new_url
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Menu item updated successfully',
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'category': {
                        'id': item.category.id,
                        'name': item.category.name
                    },
                    'price': float(item.price),
                    'image_url': item.image_url,
                    'available': item.available
                }
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating menu item: {str(e)}")
            return jsonify({'error': 'Failed to update menu item'}), 500
            
    elif request.method == 'DELETE':
        try:
            item = MenuItem.query.get_or_404(item_id)
            
            # Delete image file if it exists and is a local file
            if item.image_url and item.image_url.startswith('/static/uploads/'):
                filepath = os.path.join(app.root_path, item.image_url.lstrip('/'))
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            db.session.delete(item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Menu item deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error deleting menu item: {str(e)}")
            return jsonify({'error': 'Failed to delete menu item'}), 500

@app.route('/api/admin/categories', methods=['GET', 'POST'])
@app.route('/api/admin/categories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@admin_required
def handle_category(id=None):
    if request.method == 'GET':
        if id:
            category = Category.query.get_or_404(id)
            return jsonify({
                'id': category.id,
                'name': category.name,
                'display_name': category.display_name,
                'icon': category.icon
            })
        else:
            try:
                categories = Category.query.all()
                categories_list = []
                
                for category in categories:
                    # Count items in this category
                    items_count = MenuItem.query.filter_by(category_id=category.id).count()
                    
                    categories_list.append({
                        'id': category.id,
                        'name': category.name,
                        'display_name': category.display_name,
                        'icon': category.icon,
                        'items_count': items_count
                    })
                
                return jsonify(categories_list)
                
            except Exception as e:
                app.logger.error(f"Error getting categories: {str(e)}")
                return jsonify({'error': 'Failed to get categories'}), 500
                
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'error': 'Category name is required'}), 400
                
            # Check if category name already exists
            if Category.query.filter_by(name=data['name']).first():
                return jsonify({'error': 'Category name already exists'}), 400
                
            # Create new category
            category = Category(
                name=data['name'],
                display_name=data.get('display_name', ''),
                icon=data.get('icon', '')
            )
            
            db.session.add(category)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'display_name': category.display_name,
                    'icon': category.icon
                }
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating category: {str(e)}")
            return jsonify({'error': 'Failed to create category'}), 500
    
    elif request.method == 'PUT':
        try:
            category = Category.query.get_or_404(id)
            data = request.get_json()
            category.name = data['name']
            category.display_name = data.get('display_name', category.display_name)
            category.icon = data.get('icon', category.icon)
            
            db.session.commit()
            return jsonify({
                'success': True,
                'id': category.id,
                'name': category.name,
                'display_name': category.display_name,
                'icon': category.icon
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating category: {str(e)}")
            return jsonify({'error': 'Failed to update category'}), 500
    
    else:  # DELETE
        try:
            category = Category.query.get_or_404(id)
            
            # Check if category has menu items
            if MenuItem.query.filter_by(category_id=id).first():
                return jsonify({
                    'error': 'Cannot delete category that has menu items. Please delete or move the items first.'
                }), 400
            
            db.session.delete(category)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Category deleted successfully'})
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error deleting category: {str(e)}")
            return jsonify({'error': 'Failed to delete category'}), 500

@app.route('/api/menu')
def get_menu():
    try:
        # Get all categories and their menu items
        categories = Category.query.all()
        menu_data = []
        
        for category in categories:
            items = MenuItem.query.filter_by(category_id=category.id, available=True).all()
            if items:  # Only include categories that have items
                menu_data.append({
                    'category': category.name.lower(),
                    'display_name': category.name,
                    'items': [{
                        'id': item.id,
                        'name': item.name,
                        'description': item.description,
                        'price': float(item.price),
                        'image_url': item.image_url,
                        'available': item.available
                    } for item in items]
                })
        
        return jsonify(menu_data)
    except Exception as e:
        app.logger.error(f"Error fetching menu items: {str(e)}")
        return jsonify({'error': 'Failed to load menu items'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        app.logger.info(f"Received order data: {data}")
        
        # Validate required fields
        required_fields = ['customerName', 'customerEmail', 'items', 'totalAmount', 'paymentMethod']
        for field in required_fields:
            if field not in data:
                app.logger.error(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate a 4-digit order number
        try:
            last_order = Order.query.order_by(Order.id.desc()).first()
            if last_order:
                last_number = int(last_order.order_number)
                new_number = (last_number + 1) % 10000  # Keep it 4 digits
            else:
                new_number = 1
                
            # Pad with zeros to maintain 4 digits
            order_number = f"{new_number:04d}"
        except Exception as e:
            app.logger.error(f"Error generating order number: {str(e)}")
            return jsonify({'error': 'Failed to generate order number'}), 500
        
        try:
            # Create new order
            order = Order(
                order_number=order_number,
                customer_name=data['customerName'],
                customer_email=data['customerEmail'],
                customer_phone=data.get('customerPhone', ''),
                special_instructions=data.get('specialInstructions', ''),
                payment_method=data['paymentMethod'],
                total_amount=data['totalAmount'],
                status='pending',
                created_at=datetime.now()
            )
            db.session.add(order)
            db.session.flush()  # Get the order ID without committing
            
            app.logger.info(f"Created order: {order.order_number}")
            
            # Get all menu items at once for better performance
            menu_items = {item.id: item for item in MenuItem.query.filter(
                MenuItem.id.in_([item['id'] for item in data['items']])
            ).all()}
            
            # Create order items
            for item_data in data['items']:
                app.logger.info(f"Processing item: {item_data}")
                if not all(k in item_data for k in ['id', 'quantity', 'price']):
                    raise ValueError(f"Invalid item data: {item_data}")
                
                menu_item = menu_items.get(item_data['id'])
                if menu_item:
                    order_item = OrderItem(
                        order_id=order.id,
                        menu_item_id=menu_item.id,
                        menu_item=menu_item,  # Set the relationship
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )
                    db.session.add(order_item)
                else:
                    app.logger.error(f"Menu item not found: {item_data['id']}")
                    
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating order or order items: {str(e)}")
            return jsonify({'error': 'Failed to create order or order items'}), 500
        
        try:
            db.session.commit()
            app.logger.info("Order committed successfully")
        except Exception as e:
            app.logger.error(f"Error committing order to database: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Failed to save order to database'}), 500
        
        # Prepare response data
        response_data = {
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order_number,
                'status': order.status,
                'total': float(order.total_amount),
                'created_at': order.created_at.isoformat() if order.created_at else None
            }
        }
        
        # If it's a card payment and Stripe is configured
        if data['paymentMethod'] == 'card' and app.config.get('STRIPE_SECRET_KEY'):
            try:
                stripe.api_key = app.config['STRIPE_SECRET_KEY']
                intent = stripe.PaymentIntent.create(
                    amount=int(float(order.total_amount) * 100),  # Convert to cents
                    currency='zar',
                    metadata={
                        'order_id': order.id,
                        'order_number': order_number
                    }
                )
                response_data['client_secret'] = intent.client_secret
            except Exception as e:
                app.logger.error(f"Stripe error: {str(e)}")
                return jsonify({'error': 'Payment processing failed'}), 500
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error creating order: {str(e)}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/')
def index():
    categories = Category.query.all()
    menu_items = MenuItem.query.filter_by(available=True).all()
    return render_template('index.html', categories=categories, menu_items=menu_items)

@app.route('/payment')
def payment():
    order_id = request.args.get('order_id')
    amount = request.args.get('amount')
    
    if not order_id:
        flash('Invalid payment request', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get order details
        order = Order.query.get(order_id)
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('index'))
        
        # Initialize Stripe
        stripe.api_key = app.config['STRIPE_SECRET_KEY']
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(float(amount) * 100),  # Convert to cents
            currency='zar',
            metadata={
                'order_id': order_id,
                'order_number': order.order_number
            }
        )
        
        return render_template(
            'payment.html',
            client_secret=intent.client_secret,
            amount=amount,
            order_number=order.order_number,
            customer_email=order.customer_email,
            stripe_public_key=app.config['STRIPE_PUBLIC_KEY'],
            order_id=order_id
        )
        
    except Exception as e:
        app.logger.error(f"Payment error: {str(e)}")
        flash('Error processing payment', 'error')
        return redirect(url_for('index'))

@app.route('/payment-success')
def payment_success():
    payment_intent_id = request.args.get('payment_intent')
    order_id = request.args.get('order_id')
    
    if not order_id:
        flash('Invalid payment confirmation', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get order
        order = Order.query.get(order_id)
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('index'))
        
        # Verify payment status with Stripe
        stripe.api_key = app.config['STRIPE_SECRET_KEY']
        if payment_intent_id:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if payment_intent.status != 'succeeded':
                flash('Payment was not successful', 'error')
                return redirect(url_for('index'))
        
        # Update order status
        order.status = 'paid'
        db.session.commit()
        
        # Get order items for EmailJS
        order_items = []
        total_amount = 0
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                order_items.append({
                    'name': menu_item.name,
                    'quantity': item.quantity,
                    'price': float(menu_item.price)
                })
                total_amount += menu_item.price * item.quantity

        # Prepare order details for EmailJS
        order_details = {
            'items': order_items,
            'customerName': order.customer_name,
            'customerEmail': order.customer_email,
            'totalAmount': total_amount
        }
        
        return render_template('payment_success.html',
                             order_number=order.order_number,
                             amount=total_amount,
                             customer_email=order.customer_email,
                             order_details=json.dumps(order_details),
                             current_time=datetime.now())
                             
    except Exception as e:
        print(f"Error processing payment success: {e}")
        flash('An error occurred while processing your payment', 'error')
        return redirect(url_for('index'))

@app.route('/api/order/<int:order_id>')
@login_required
def get_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        # Get order items
        items = OrderItem.query.filter_by(order_id=order.id).all()
        items_list = []
        for item in items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                items_list.append({
                    'name': menu_item.name,
                    'quantity': item.quantity,
                    'price': float(menu_item.price)
                })
        
        # Convert UTC time to local time
        local_tz = pytz.timezone('Africa/Johannesburg')
        local_time = order.created_at.replace(tzinfo=pytz.UTC).astimezone(local_tz)
        
        order_data = {
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'customer_phone': order.customer_phone,
                'status': order.status,
                'total_amount': float(order.total_amount),
                'created_at': local_time.isoformat(),
                'special_instructions': order.special_instructions,
                'items': items_list
            }
        }
        
        return jsonify(order_data)
        
    except Exception as e:
        app.logger.error(f"Error getting order details: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load order details'
        }), 500

@app.route('/api/admin/orders')
@login_required
def get_filtered_orders():
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        date = request.args.get('date', '')
        search = request.args.get('search', '')
        
        # Start with base query with eager loading
        query = Order.query.options(
            db.joinedload(Order.items).joinedload(OrderItem.menu_item)
        )
        
        # Apply status filter
        if status and status != 'all':
            query = query.filter(Order.status == status)
            
        # Apply date filter
        if date:
            try:
                filter_date = datetime.strptime(date, '%Y-%m-%d').date()
                local_tz = pytz.timezone('Africa/Johannesburg')
                day_start = datetime.combine(filter_date, time.min).astimezone(local_tz)
                day_end = datetime.combine(filter_date, time.max).astimezone(local_tz)
                query = query.filter(Order.created_at.between(day_start, day_end))
            except ValueError:
                pass  # Invalid date format, ignore filter
                
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Order.order_number.ilike(search_term),
                    Order.customer_name.ilike(search_term),
                    Order.customer_email.ilike(search_term)
                )
            )
            
        # Get orders ordered by creation date (newest first)
        orders = query.order_by(Order.created_at.desc()).all()
        
        orders_list = []
        for order in orders:
            # Process order items with proper error handling
            items_text = []
            try:
                for order_item in order.items:
                    menu_item = order_item.menu_item
                    if menu_item:
                        items_text.append(f"{menu_item.name} x{order_item.quantity}")
                    else:
                        app.logger.warning(f"Menu item not found for order item {order_item.id}")
            except Exception as e:
                app.logger.error(f"Error processing items for order {order.id}: {str(e)}")
                items_text = ['Error loading items']
            
            # Convert UTC time to local time
            local_tz = pytz.timezone('Africa/Johannesburg')
            local_time = order.created_at.replace(tzinfo=pytz.UTC).astimezone(local_tz)
            
            order_data = {
                'id': order.id,
                'order_number': f"{int(order.order_number):04d}",
                'customer': order.customer_name,
                'items': ', '.join(items_text) if items_text else 'No items',
                'total': float(order.total_amount),
                'status': order.status,
                'created_at': local_time.isoformat()
            }
            
            app.logger.info(f"Processed order data: {order_data}")
            orders_list.append(order_data)
        
        return jsonify(orders_list)
        
    except Exception as e:
        app.logger.error(f"Error getting filtered orders: {str(e)}")
        app.logger.exception(e)  # Log full stack trace
        return jsonify([])

@app.route('/api/admin/debug/order-items/<int:order_id>')
@login_required
def debug_order_items(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        items = OrderItem.query.filter_by(order_id=order.id).all()
        
        items_data = []
        for item in items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            items_data.append({
                'id': item.id,
                'menu_item_id': item.menu_item_id,
                'menu_item_name': menu_item.name if menu_item else 'Unknown',
                'quantity': item.quantity,
                'price': float(item.price)
            })
            
        return jsonify({
            'order_id': order.id,
            'order_number': order.order_number,
            'items': items_data
        })
    except Exception as e:
        app.logger.error(f"Error debugging order items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/categories')
@login_required
@admin_required
def admin_categories():
    return render_template('admin/categories.html')
