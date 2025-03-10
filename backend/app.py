from quart import Quart, request, jsonify
from sqlalchemy import select
from models import Base, User
import bcrypt
import jwt
from datetime import datetime, timedelta
from utils import token_required, async_session, engine, SECRET_KEY
from routes.flashcards import flashcard_bp
from routes.timetable import timetable_bp
from routes.classes import class_bp

app = Quart(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.before_serving
async def startup():
    await init_db()

@app.route('/register', methods=['POST'])
async def register():
    data = await request.get_json()
    
    if not all(k in data for k in ['username', 'password', 'email']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Password validation
    if len(data['password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
    
    async with async_session() as session:
        # Check if username exists
        result = await session.execute(
            select(User).where(User.username == data['username'])
        )
        if result.scalar_one_or_none():
            return jsonify({'message': 'Username already exists'}), 400

        # Hash password
        hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        new_user = User(
            username=data['username'],
            password=hashed.decode('utf-8'),
            email=data['email'],
            recovery_email=data.get('recovery_email')
        )
        session.add(new_user)
        await session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
async def login():
    data = await request.get_json()
    
    if not all(k in data for k in ['username', 'password']):
        return jsonify({'message': 'Missing username or password'}), 400
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == data['username'])
        )
        user = result.scalar_one_or_none()
        
        if user and bcrypt.checkpw(data['password'].encode('utf-8'), 
                                 user.password.encode('utf-8')):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['SECRET_KEY'])
            
            return jsonify({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/user/profile', methods=['GET'])
@token_required
async def get_profile(current_user):
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'xp': current_user.xp,
        'created_at': current_user.created_at.isoformat()
    })

@app.route('/user/change-password', methods=['POST'])
@token_required
async def change_password(current_user):
    data = await request.get_json()
    
    if not all(k in data for k in ['old_password', 'new_password']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if len(data['new_password']) < 8:
        return jsonify({'message': 'New password must be at least 8 characters'}), 400
    
    if not bcrypt.checkpw(data['old_password'].encode('utf-8'), 
                         current_user.password.encode('utf-8')):
        return jsonify({'message': 'Invalid old password'}), 401
    
    async with async_session() as session:
        current_user.password = bcrypt.hashpw(
            data['new_password'].encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        await session.commit()
    
    return jsonify({'message': 'Password updated successfully'})

@app.route('/user/titles', methods=['GET'])
@token_required
async def get_titles(current_user):
    async with async_session() as session:
        result = await session.execute(
            select(UserTitle).where(UserTitle.user_id == current_user.id)
            .order_by(UserTitle.unlocked_at.desc())
        )
        titles = result.scalars().all()
        return jsonify([{
            'title': t.title,
            'unlocked_at': t.unlocked_at.isoformat()
        } for t in titles])

@app.route('/user/tests', methods=['GET'])
@token_required
async def get_tests(current_user):
    async with async_session() as session:
        result = await session.execute(
            select(Test)
            .where(Test.user_id == current_user.id)
            .order_by(Test.completed_at.desc())
            .limit(10)
        )
        tests = result.scalars().all()
        return jsonify([{
            'score': t.score,
            'completed_at': t.completed_at.isoformat(),
            'duration': t.duration
        } for t in tests])

# Register blueprints
app.register_blueprint(flashcard_bp, url_prefix='/flashcard')
app.register_blueprint(timetable_bp, url_prefix='/timetable')
app.register_blueprint(class_bp, url_prefix='/class')

if __name__ == '__main__':
    app.run()
