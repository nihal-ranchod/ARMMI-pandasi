from flask import Blueprint, request, jsonify, session
from auth.models import User
from auth.decorators import login_required, create_user_session, clear_user_session, get_current_user
import re
import os
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, ""

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate input
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        password = data.get('password', '')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        if not password:
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password requirements
        password_valid, password_error = validate_password(password)
        if not password_valid:
            return jsonify({'success': False, 'error': password_error}), 400
        
        # Create regular user (admin creation requires special route)
        user, error = User.create_user(email, name, password, role='user')
        
        if not user:
            return jsonify({'success': False, 'error': error}), 409 if 'already exists' in error else 500
        
        # Create session for new user
        if not create_user_session(user):
            return jsonify({'success': False, 'error': 'User created but failed to create session'}), 500
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_admin': user.is_admin(),
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error in registration: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred during registration'}), 500

@auth_bp.route('/register-admin', methods=['POST'])
def register_admin():
    """Register a new admin user with admin key validation"""
    try:
        data = request.get_json()
        
        # Validate input
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        password = data.get('password', '')
        admin_key = data.get('admin_key', '')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        if not password:
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        if not admin_key:
            return jsonify({'success': False, 'error': 'Admin key is required'}), 400
        
        # Validate admin key
        expected_admin_key = os.getenv('ADMIN_REGISTRATION_KEY')
        if not expected_admin_key:
            logger.error("ADMIN_REGISTRATION_KEY environment variable not set")
            return jsonify({'success': False, 'error': 'Admin registration not configured'}), 500
        
        if admin_key != expected_admin_key:
            logger.warning(f"Invalid admin key attempted for email: {email}")
            return jsonify({'success': False, 'error': 'Invalid admin key'}), 403
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password requirements
        password_valid, password_error = validate_password(password)
        if not password_valid:
            return jsonify({'success': False, 'error': password_error}), 400
        
        # Create admin user
        user, error = User.create_user(email, name, password, role='admin')
        
        if not user:
            return jsonify({'success': False, 'error': error}), 409 if 'already exists' in error else 500
        
        # Create session for new admin user
        if not create_user_session(user):
            return jsonify({'success': False, 'error': 'Admin created but failed to create session'}), 500
        
        logger.info(f"New admin user registered: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Admin account created successfully',
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_admin': user.is_admin(),
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error in admin registration: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred during admin registration'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and create session"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.find_by_email(email)
        if not user:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not user.verify_password(password):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Create session
        if not create_user_session(user):
            return jsonify({'success': False, 'error': 'Failed to create session'}), 500
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_admin': user.is_admin(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred during login'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    try:
        user_email = session.get('user_email')
        
        if clear_user_session():
            if user_email:
                logger.info(f"User logged out: {user_email}")
            
            return jsonify({
                'success': True,
                'message': 'Logout successful'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to logout'}), 500
            
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred during logout'}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user_info():
    """Get current user information"""
    try:
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get user stats
        dataset_count = len(current_user.datasets)
        query_count = len(current_user.query_history)
        
        return jsonify({
            'success': True,
            'user': {
                'user_id': current_user.user_id,
                'email': current_user.email,
                'name': current_user.name,
                'role': current_user.role,
                'is_admin': current_user.is_admin(),
                'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
                'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
                'stats': {
                    'datasets': dataset_count,
                    'queries': query_count
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500

@auth_bp.route('/check', methods=['GET'])
def check_authentication():
    """Check if user is authenticated"""
    try:
        current_user = get_current_user()
        
        if current_user:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': {
                    'user_id': current_user.user_id,
                    'email': current_user.email,
                    'name': current_user.name,
                    'role': current_user.role,
                    'is_admin': current_user.is_admin()
                }
            })
        else:
            return jsonify({
                'success': True,
                'authenticated': False
            })
            
    except Exception as e:
        logger.error(f"Error checking authentication: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500