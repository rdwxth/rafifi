from quart import Blueprint, request, jsonify
from sqlalchemy import select
from models import User, UserTitle
import bcrypt
import jwt
from datetime import datetime, timedelta
from utils import token_required, async_session, SECRET_KEY
import re
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, None

@auth_bp.route('/register', methods=['POST'])
async def register():
    try:
        data = await request.get_json()
        logger.info(f"Registration attempt for username: {data.get('username')}")
        
        required_fields = ['username', 'password', 'email']
        if not all(k in data for k in required_fields):
            logger.warning("Missing required fields in registration request")
            return jsonify({'message': 'Missing required fields'}), 400
        
        # Password validation
        is_valid, error_msg = validate_password(data['password'])
        if not is_valid:
            logger.warning(f"Password validation failed: {error_msg}")
            return jsonify({'message': error_msg}), 400
        
        # Email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            logger.warning("Invalid email format")
            return jsonify({'message': 'Invalid email format'}), 400
        
        # Create database session
        async with async_session() as session:
            try:
                # Check if username exists
                result = await session.execute(
                    select(User).where(User.username == data['username'])
                )
                if result.scalar_one_or_none():
                    logger.warning(f"Username already exists: {data['username']}")
                    return jsonify({'message': 'Username already exists'}), 400
                    
                # Check if email exists
                result = await session.execute(
                    select(User).where(User.email == data['email'])
                )
                if result.scalar_one_or_none():
                    logger.warning(f"Email already exists: {data['email']}")
                    return jsonify({'message': 'Email already exists'}), 400

                # Hash password
                hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
                
                # Create new user
                new_user = User(
                    username=data['username'],
                    password=hashed,  # Store as bytes directly
                    email=data['email'],
                    xp=0,
                    created_at=datetime.utcnow()
                )
                session.add(new_user)
                await session.flush()  # Get user ID
                
                # Add initial title
                beginner_title = UserTitle(
                    user_id=new_user.id,
                    title="Beginner",
                    earned_at=datetime.utcnow()
                )
                session.add(beginner_title)
                await session.commit()
                
                logger.info(f"Successfully registered user: {data['username']}")
                return jsonify({
                    'message': 'User created successfully',
                    'user_id': new_user.id,
                    'username': new_user.username
                }), 201
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error during registration: {str(e)}\n{traceback.format_exc()}")
                raise
            
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'message': f'Internal server error: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
async def login():
    try:
        data = await request.get_json()
        logger.info(f"Login attempt for username: {data.get('username')}")
        
        if not all(k in data for k in ['username', 'password']):
            logger.warning("Missing username or password in login request")
            return jsonify({'message': 'Missing username or password'}), 400
        
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(User).where(User.username == data['username'])
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"User not found: {data['username']}")
                    return jsonify({'message': 'Invalid credentials'}), 401
                
                # Compare passwords directly as bytes
                if bcrypt.checkpw(data['password'].encode('utf-8'), user.password):
                    token = jwt.encode({
                        'user_id': user.id,
                        'exp': datetime.utcnow() + timedelta(hours=24)
                    }, SECRET_KEY)
                    
                    logger.info(f"Successful login for user: {data['username']}")
                    return jsonify({
                        'token': token,
                        'user_id': user.id,
                        'username': user.username
                    })
                else:
                    logger.warning(f"Invalid password for user: {data['username']}")
                    return jsonify({'message': 'Invalid credentials'}), 401
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error during login: {str(e)}\n{traceback.format_exc()}")
                raise
                    
    except Exception as e:
        logger.error(f"Error during login: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'message': f'Internal server error: {str(e)}'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
async def change_password(current_user):
    try:
        data = await request.get_json()
        logger.info(f"Password change attempt for user: {current_user.username}")
        
        if not all(k in data for k in ['old_password', 'new_password']):
            logger.warning("Missing required fields in password change request")
            return jsonify({'message': 'Missing required fields'}), 400
        
        # Validate new password
        is_valid, error_msg = validate_password(data['new_password'])
        if not is_valid:
            logger.warning(f"New password validation failed: {error_msg}")
            return jsonify({'message': error_msg}), 400
        
        if not bcrypt.checkpw(data['old_password'].encode('utf-8'), current_user.password):
            logger.warning(f"Invalid old password for user: {current_user.username}")
            return jsonify({'message': 'Invalid old password'}), 401
        
        async with async_session() as session:
            try:
                current_user.password = bcrypt.hashpw(
                    data['new_password'].encode('utf-8'), 
                    bcrypt.gensalt()
                )
                await session.commit()
                
                logger.info(f"Successfully changed password for user: {current_user.username}")
                return jsonify({'message': 'Password updated successfully'})
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error during password change: {str(e)}\n{traceback.format_exc()}")
                raise
            
    except Exception as e:
        logger.error(f"Error during password change: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'message': f'Internal server error: {str(e)}'}), 500

@auth_bp.route('/change-recovery-email', methods=['POST'])
@token_required
async def change_recovery_email(current_user):
    try:
        data = await request.get_json()
        logger.info(f"Recovery email change attempt for user: {current_user.username}")
        
        if 'recovery_email' not in data:
            logger.warning("Missing recovery email in recovery email change request")
            return jsonify({'message': 'Missing recovery email'}), 400
        
        # Email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['recovery_email']):
            logger.warning("Invalid email format")
            return jsonify({'message': 'Invalid email format'}), 400
        
        async with async_session() as session:
            try:
                current_user.recovery_email = data['recovery_email']
                await session.commit()
                
                logger.info(f"Successfully changed recovery email for user: {current_user.username}")
                return jsonify({'message': 'Recovery email updated successfully'})
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error during recovery email change: {str(e)}\n{traceback.format_exc()}")
                raise
            
    except Exception as e:
        logger.error(f"Error during recovery email change: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'message': f'Internal server error: {str(e)}'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
async def reset_password():
    try:
        data = await request.get_json()
        logger.info("Password reset attempt")
        
        if not all(k in data for k in ['email', 'recovery_email']):
            logger.warning("Missing required fields in password reset request")
            return jsonify({'message': 'Missing required fields'}), 400
        
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(User)
                    .where(User.email == data['email'])
                    .where(User.recovery_email == data['recovery_email'])
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.warning("Invalid email or recovery email for password reset")
                    return jsonify({'message': 'Invalid email or recovery email'}), 404
                    
                # Generate temporary password
                temp_password = "TempPass123!"  # In production, generate a secure random password
                
                user.password = bcrypt.hashpw(
                    temp_password.encode('utf-8'),
                    bcrypt.gensalt()
                )
                await session.commit()
                
                logger.info(f"Successfully reset password for user: {user.username}")
                return jsonify({
                    'message': 'Password reset successful. Check your email for the temporary password.',
                    'temp_password': temp_password  # Remove in production
                })
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error during password reset: {str(e)}\n{traceback.format_exc()}")
                raise
                
    except Exception as e:
        logger.error(f"Error during password reset: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'message': f'Internal server error: {str(e)}'}), 500
