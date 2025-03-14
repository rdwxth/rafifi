from quart import Blueprint, request, jsonify
from sqlalchemy import select, func, desc, delete
from models import FlashcardSet, Flashcard, Test, User
from utils import token_required, generate_hash_key
from database import db
from datetime import datetime

flashcard_bp = Blueprint('flashcard', __name__)

@flashcard_bp.route('/sets', methods=['GET'])
@token_required
async def get_flashcard_sets(current_user):
    async with db.session() as session:
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.user_id == current_user.id)
            .order_by(FlashcardSet.created_at.desc())
        )
        sets = result.scalars().all()
        
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'folder': s.folder,
            'card_count': len(s.flashcards),
            'created_at': s.created_at.isoformat()
        } for s in sets])

@flashcard_bp.route('/sets', methods=['POST'])
@token_required
async def create_flashcard_set(current_user):
    data = await request.get_json()
    
    if 'name' not in data:
        return jsonify({'message': 'Missing name'}), 400
    
    async with db.session() as session:
        new_set = FlashcardSet(
            name=data['name'],
            folder=data.get('folder', 'General'),
            user_id=current_user.id,
            hash_key=generate_hash_key('set', current_user.id, data['name'])
        )
        session.add(new_set)
        await session.commit()
        await session.refresh(new_set)
        
        return jsonify({
            'id': new_set.id,
            'name': new_set.name,
            'folder': new_set.folder,
            'card_count': 0,
            'created_at': new_set.created_at.isoformat()
        }), 201

@flashcard_bp.route('/sets/<int:set_id>', methods=['GET'])
@token_required
async def get_flashcard_set(current_user, set_id):
    async with db.session() as session:
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
            .where(FlashcardSet.user_id == current_user.id)
        )
        set_ = result.scalar_one_or_none()
        
        if not set_:
            return jsonify({'message': 'Set not found'}), 404
        
        return jsonify({
            'id': set_.id,
            'name': set_.name,
            'folder': set_.folder,
            'flashcards': [{
                'id': card.id,
                'front': card.front,
                'back': card.back,
                'difficulty': card.difficulty,
                'created_at': card.created_at.isoformat()
            } for card in set_.flashcards],
            'created_at': set_.created_at.isoformat()
        })

@flashcard_bp.route('/sets/<int:set_id>/cards', methods=['POST'])
@token_required
async def create_flashcard(current_user, set_id):
    data = await request.get_json()
    
    if not all(k in data for k in ['front', 'back']):
        return jsonify({'message': 'Missing front or back content'}), 400
    
    async with db.session() as session:
        # Verify set ownership
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
            .where(FlashcardSet.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            return jsonify({'message': 'Set not found'}), 404
        
        new_card = Flashcard(
            front=data['front'],
            back=data['back'],
            difficulty=data.get('difficulty', 'medium'),
            set_id=set_id,
            hash_key=generate_hash_key('card', set_id, data['front'], data['back'])
        )
        session.add(new_card)
        await session.commit()
        await session.refresh(new_card)
        
        return jsonify({
            'id': new_card.id,
            'front': new_card.front,
            'back': new_card.back,
            'difficulty': new_card.difficulty,
            'created_at': new_card.created_at.isoformat()
        }), 201

@flashcard_bp.route('/sets/<int:set_id>/cards/<int:card_id>', methods=['PUT'])
@token_required
async def update_flashcard(current_user, set_id, card_id):
    data = await request.get_json()
    
    async with db.session() as session:
        # Verify set ownership
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
            .where(FlashcardSet.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            return jsonify({'message': 'Set not found'}), 404
        
        # Get card
        result = await session.execute(
            select(Flashcard)
            .where(Flashcard.id == card_id)
            .where(Flashcard.set_id == set_id)
        )
        card = result.scalar_one_or_none()
        
        if not card:
            return jsonify({'message': 'Card not found'}), 404
        
        # Update fields
        if 'front' in data:
            card.front = data['front']
            card.hash_key = generate_hash_key('card', set_id, data['front'], card.back)
        if 'back' in data:
            card.back = data['back']
            card.hash_key = generate_hash_key('card', set_id, card.front, data['back'])
        if 'difficulty' in data:
            card.difficulty = data['difficulty']
        
        await session.commit()
        
        return jsonify({
            'id': card.id,
            'front': card.front,
            'back': card.back,
            'difficulty': card.difficulty,
            'created_at': card.created_at.isoformat()
        })

@flashcard_bp.route('/sets/<int:set_id>/cards/<int:card_id>', methods=['DELETE'])
@token_required
async def delete_flashcard(current_user, set_id, card_id):
    async with db.session() as session:
        # Verify set ownership
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
            .where(FlashcardSet.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            return jsonify({'message': 'Set not found'}), 404
        
        # Get card
        result = await session.execute(
            select(Flashcard)
            .where(Flashcard.id == card_id)
            .where(Flashcard.set_id == set_id)
        )
        card = result.scalar_one_or_none()
        
        if not card:
            return jsonify({'message': 'Card not found'}), 404
        
        await session.delete(card)
        await session.commit()
        
        return '', 204

@flashcard_bp.route('/folders', methods=['GET'])
@token_required
async def get_folders(current_user):
    async with db.session() as session:
        result = await session.execute(
            select(FlashcardSet.folder)
            .where(FlashcardSet.user_id == current_user.id)
            .distinct()
        )
        folders = result.scalars().all()
        
        return jsonify(folders)

@flashcard_bp.route('/search', methods=['GET'])
@token_required
async def search_flashcards(current_user):
    query = request.args.get('q', '')
    folder = request.args.get('folder', None)
    
    async with db.session() as session:
        # Build base query
        base_query = (
            select(FlashcardSet)
            .where(FlashcardSet.user_id == current_user.id)
        )
        
        # Add folder filter if specified
        if folder:
            base_query = base_query.where(FlashcardSet.folder == folder)
        
        # Add search filter if query provided
        if query:
            base_query = base_query.where(FlashcardSet.name.ilike(f'%{query}%'))
        
        result = await session.execute(base_query)
        sets = result.scalars().all()
        
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'folder': s.folder,
            'card_count': len(s.flashcards),
            'created_at': s.created_at.isoformat()
        } for s in sets])

@flashcard_bp.route('/sets/<int:set_id>/cards', methods=['GET'])
@token_required
async def get_flashcards(current_user, set_id):
    sort_by = request.args.get('sort', 'difficulty')
    order = request.args.get('order', 'asc')
    
    async with db.session() as session:
        flashcard_set = await session.get(FlashcardSet, set_id)
        if not flashcard_set or flashcard_set.user_id != current_user.id:
            return jsonify({'message': 'Flashcard set not found'}), 404
            
        query = select(Flashcard).where(Flashcard.set_id == set_id)
        
        if sort_by == 'difficulty':
            query = query.order_by(
                desc(Flashcard.difficulty) if order == 'desc' 
                else Flashcard.difficulty
            )
            
        result = await session.execute(query)
        cards = result.scalars().all()
        
        return jsonify([{
            'id': c.id,
            'question': c.front,
            'answer': c.back,
            'difficulty': c.difficulty
        } for c in cards])

@flashcard_bp.route('/sets/<int:set_id>/test', methods=['POST'])
@token_required
async def submit_test(current_user, set_id):
    data = await request.get_json()
    
    if not all(k in data for k in ['score', 'duration']):
        return jsonify({'message': 'Missing score or duration'}), 400
    
    async with db.session() as session:
        # Verify set exists and user has access
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
            .where(FlashcardSet.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            return jsonify({'message': 'Set not found'}), 404
        
        # Create test record
        test = Test(
            user_id=current_user.id,
            flashcard_set_id=set_id,
            score=data['score'],
            duration=data['duration']
        )
        session.add(test)
        
        # Calculate XP gain (example formula)
        xp_gain = int(data['score'] * 10)  # 10 XP per correct answer
        current_user.xp += xp_gain
        
        await session.commit()
        
        return jsonify({
            'message': 'Test submitted successfully',
            'xp_gained': xp_gain
        }), 201

@flashcard_bp.route('/sets/<int:set_id>', methods=['PUT'])
@token_required
async def update_flashcard_set(current_user, set_id):
    data = await request.get_json()
    
    if 'name' not in data:
        return jsonify({'message': 'Missing name'}), 400
    
    async with db.session() as session:
        # Verify set ownership
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
            .where(FlashcardSet.user_id == current_user.id)
        )
        set_ = result.scalar_one_or_none()
        
        if not set_:
            return jsonify({'message': 'Set not found'}), 404
            
        # Update set
        set_.name = data['name']
        set_.folder = data.get('folder', 'General')
        set_.hash_key = generate_hash_key('set', current_user.id, data['name'])
        await session.commit()
        
        return jsonify({
            'id': set_.id,
            'name': set_.name,
            'folder': set_.folder,
            'created_at': set_.created_at.isoformat()
        })

@flashcard_bp.route('/sets/<int:set_id>/cards', methods=['PUT'])
@token_required
async def update_flashcard_set_cards(current_user, set_id):
    data = await request.get_json()
    
    if 'cards' not in data:
        return jsonify({'message': 'Missing cards data'}), 400
    
    async with db.session() as session:
        # Verify set ownership
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
            .where(FlashcardSet.user_id == current_user.id)
        )
        set_ = result.scalar_one_or_none()
        
        if not set_:
            return jsonify({'message': 'Set not found'}), 404
            
        # Delete existing cards
        await session.execute(
            delete(Flashcard).where(Flashcard.set_id == set_id)
        )
        
        # Add new cards
        for card_data in data['cards']:
            new_card = Flashcard(
                front=card_data['front'],
                back=card_data['back'],
                difficulty=card_data.get('difficulty', 'medium'),
                set_id=set_id,
                hash_key=generate_hash_key('card', set_id, card_data['front'], card_data['back'])
            )
            session.add(new_card)
        
        await session.commit()
        
        # Return updated set
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
        )
        set_ = result.scalar_one()
        
        return jsonify({
            'id': set_.id,
            'name': set_.name,
            'folder': set_.folder,
            'flashcards': [{
                'id': card.id,
                'front': card.front,
                'back': card.back,
                'difficulty': card.difficulty,
                'created_at': card.created_at.isoformat()
            } for card in set_.flashcards],
            'created_at': set_.created_at.isoformat()
        })

@flashcard_bp.route('/sets/<int:set_id>', methods=['DELETE'])
@token_required
async def delete_flashcard_set(current_user, set_id):
    async with db.session() as session:
        # Verify set ownership
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == set_id)
            .where(FlashcardSet.user_id == current_user.id)
        )
        set_ = result.scalar_one_or_none()
        
        if not set_:
            return jsonify({'message': 'Set not found'}), 404
            
        await session.delete(set_)
        await session.commit()
        
        return '', 204

@flashcard_bp.route('/sets/copy', methods=['POST'])
@token_required
async def copy_flashcard_set(current_user):
    data = await request.get_json()
    
    if 'set_id' not in data:
        return jsonify({'message': 'Missing set_id'}), 400
    
    async with db.session() as session:
        # Get original set
        result = await session.execute(
            select(FlashcardSet)
            .where(FlashcardSet.id == data['set_id'])
        )
        original_set = result.scalar_one_or_none()
        
        if not original_set:
            return jsonify({'message': 'Set not found'}), 404
            
        # Create new set
        new_set = FlashcardSet(
            name=f"{original_set.name} (Copy)",
            folder=original_set.folder,
            user_id=current_user.id,
            hash_key=generate_hash_key('set', current_user.id, f"{original_set.name} (Copy)")
        )
        session.add(new_set)
        await session.flush()  # Get new set ID
        
        # Copy cards
        for card in original_set.flashcards:
            new_card = Flashcard(
                front=card.front,
                back=card.back,
                difficulty=card.difficulty,
                set_id=new_set.id,
                hash_key=generate_hash_key('card', new_set.id, card.front, card.back)
            )
            session.add(new_card)
        
        await session.commit()
        
        return jsonify({
            'id': new_set.id,
            'name': new_set.name,
            'folder': new_set.folder,
            'created_at': new_set.created_at.isoformat()
        }), 201
