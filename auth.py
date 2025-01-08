from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import LoginManager, current_user

login_manager = LoginManager()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be logged in as an admin to access this page.', 'error')
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
