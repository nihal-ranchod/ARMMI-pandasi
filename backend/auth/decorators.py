from functools import wraps
from flask import session, request, jsonify
from auth.models import User
import logging

logger = logging.getLogger(__name__)

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False, 
                'error': 'Authentication required',
                'auth_error': True
            }), 401
        
        # Get current user
        current_user = User.find_by_id(session['user_id'])
        if not current_user:
            # Clear invalid session
            session.clear()
            return jsonify({
                'success': False, 
                'error': 'Invalid session, please login again',
                'auth_error': True
            }), 401
        
        # Add user to request context
        request.current_user = current_user
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get current authenticated user from session"""
    if 'user_id' in session:
        return User.find_by_id(session['user_id'])
    return None

def create_user_session(user):
    """Create user session after successful authentication"""
    try:
        session.permanent = True
        session['user_id'] = user.user_id
        session['user_email'] = user.email
        session['user_name'] = user.name
        session['user_role'] = user.role
        session['is_admin'] = user.is_admin()
        
        # Update last login
        user.update_last_login()
        
        logger.info(f"Created session for user: {user.email} (role: {user.role})")
        return True
    except Exception as e:
        logger.error(f"Error creating user session: {str(e)}")
        return False

def admin_required(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False, 
                'error': 'Authentication required',
                'auth_error': True
            }), 401
        
        # Get current user
        current_user = User.find_by_id(session['user_id'])
        if not current_user:
            # Clear invalid session
            session.clear()
            return jsonify({
                'success': False, 
                'error': 'Invalid session, please login again',
                'auth_error': True
            }), 401
        
        # Check admin role
        if not current_user.is_admin():
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        # Add user to request context
        request.current_user = current_user
        return f(*args, **kwargs)
    
    return decorated_function

def clear_user_session():
    """Clear user session"""
    try:
        session.clear()
        logger.info("User session cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing user session: {str(e)}")
        return False