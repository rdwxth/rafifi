from functools import wraps
from quart import request, jsonify
import jwt
import hashlib
from datetime import datetime
from database import db

# Configuration
DATABASE_URL = "sqlite+aiosqlite:///database/rafifi.db"
SECRET_KEY = "your-secret-key-here"  # Fixed secret key for development

# Initialize database
db.init(DATABASE_URL)

def generate_hash_key(prefix, *args):
    """Generate a hash key for database objects"""
    timestamp = datetime.utcnow().timestamp()
    data = f"{prefix}:{':'.join(str(arg) for arg in args)}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()

def token_required(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            # Import here to avoid circular imports
            from models import User
            async with db.session() as session:
                result = await session.execute(
                    select(User).where(User.id == data['id'])
                )
                current_user = result.scalar_one_or_none()
                
                if current_user is None:
                    return jsonify({'message': 'Invalid token'}), 401
                    
                return await f(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}'}), 401
    
    return decorated
