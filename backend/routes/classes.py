from quart import Blueprint, request, jsonify
from sqlalchemy import select
from models import Class, ClassMember, User
from utils import token_required, async_session
import secrets

class_bp = Blueprint('class', __name__)

@class_bp.route('/', methods=['GET'])
@token_required
async def get_classes(current_user):
    async with async_session() as session:
        # Get classes where user is a member
        result = await session.execute(
            select(Class, ClassMember)
            .join(ClassMember, Class.id == ClassMember.class_id)
            .where(ClassMember.user_id == current_user.id)
        )
        classes = result.all()
        
        response = []
        for class_, member in classes:
            # Get member count
            member_count = await session.execute(
                select(ClassMember)
                .where(ClassMember.class_id == class_.id)
            )
            count = len(member_count.scalars().all())
            
            response.append({
                'id': class_.id,
                'name': class_.name,
                'code': class_.code,
                'is_leader': class_.leader_id == current_user.id,
                'member_count': count,
                'created_at': class_.created_at.isoformat()
            })
        
        return jsonify(response)

@class_bp.route('/', methods=['POST'])
@token_required
async def create_class(current_user):
    data = await request.get_json()
    
    if 'name' not in data:
        return jsonify({'message': 'Missing name'}), 400
    
    async with async_session() as session:
        # Generate unique class code
        while True:
            code = secrets.token_hex(3).upper()
            result = await session.execute(
                select(Class).where(Class.code == code)
            )
            if not result.scalar_one_or_none():
                break
        
        new_class = Class(
            name=data['name'],
            code=code,
            leader_id=current_user.id
        )
        session.add(new_class)
        await session.commit()
        
        # Add creator as first member
        member = ClassMember(
            class_id=new_class.id,
            user_id=current_user.id
        )
        session.add(member)
        await session.commit()
        
        return jsonify({
            'id': new_class.id,
            'name': new_class.name,
            'code': new_class.code,
            'is_leader': True,
            'member_count': 1,
            'created_at': new_class.created_at.isoformat()
        }), 201

@class_bp.route('/join', methods=['POST'])
@token_required
async def join_class(current_user):
    data = await request.get_json()
    
    if 'code' not in data:
        return jsonify({'message': 'Missing class code'}), 400
    
    async with async_session() as session:
        # Find class by code
        class_result = await session.execute(
            select(Class).where(Class.code == data['code'].upper())
        )
        class_ = class_result.scalar_one_or_none()
        
        if not class_:
            return jsonify({'message': 'Class not found'}), 404
        
        # Check if already a member
        member_result = await session.execute(
            select(ClassMember)
            .where(ClassMember.class_id == class_.id)
            .where(ClassMember.user_id == current_user.id)
        )
        if member_result.scalar_one_or_none():
            return jsonify({'message': 'Already a member of this class'}), 400
        
        # Add as member
        member = ClassMember(
            class_id=class_.id,
            user_id=current_user.id
        )
        session.add(member)
        await session.commit()
        
        # Get updated member count
        member_count = await session.execute(
            select(ClassMember)
            .where(ClassMember.class_id == class_.id)
        )
        count = len(member_count.scalars().all())
        
        return jsonify({
            'id': class_.id,
            'name': class_.name,
            'code': class_.code,
            'is_leader': False,
            'member_count': count,
            'created_at': class_.created_at.isoformat()
        })

@class_bp.route('/<int:class_id>/members', methods=['GET'])
@token_required
async def get_class_members(current_user, class_id):
    async with async_session() as session:
        # Verify class membership
        member_result = await session.execute(
            select(ClassMember)
            .where(ClassMember.class_id == class_id)
            .where(ClassMember.user_id == current_user.id)
        )
        if not member_result.scalar_one_or_none():
            return jsonify({'message': 'Class not found'}), 404
        
        # Get class details
        class_result = await session.execute(
            select(Class).where(Class.id == class_id)
        )
        class_ = class_result.scalar_one_or_none()
        
        # Get all members with their user info
        members_result = await session.execute(
            select(User, ClassMember)
            .join(ClassMember, User.id == ClassMember.user_id)
            .where(ClassMember.class_id == class_id)
        )
        members = members_result.all()
        
        return jsonify({
            'class': {
                'id': class_.id,
                'name': class_.name,
                'code': class_.code,
                'created_at': class_.created_at.isoformat()
            },
            'members': [{
                'id': user.id,
                'username': user.username,
                'is_leader': user.id == class_.leader_id,
                'joined_at': member.created_at.isoformat()
            } for user, member in members]
        })

@class_bp.route('/<int:class_id>/members/<int:user_id>', methods=['DELETE'])
@token_required
async def remove_member(current_user, class_id, user_id):
    async with async_session() as session:
        # Verify class exists and current user is leader
        class_result = await session.execute(
            select(Class)
            .where(Class.id == class_id)
            .where(Class.leader_id == current_user.id)
        )
        if not class_result.scalar_one_or_none():
            return jsonify({'message': 'Not authorized'}), 403
        
        # Cannot remove self if leader
        if user_id == current_user.id:
            return jsonify({'message': 'Cannot remove class leader'}), 400
        
        # Remove member
        member_result = await session.execute(
            select(ClassMember)
            .where(ClassMember.class_id == class_id)
            .where(ClassMember.user_id == user_id)
        )
        member = member_result.scalar_one_or_none()
        
        if not member:
            return jsonify({'message': 'Member not found'}), 404
        
        await session.delete(member)
        await session.commit()
        
        return '', 204

@class_bp.route('/<int:class_id>/leave', methods=['POST'])
@token_required
async def leave_class(current_user, class_id):
    async with async_session() as session:
        # Verify class exists
        class_result = await session.execute(
            select(Class).where(Class.id == class_id)
        )
        class_ = class_result.scalar_one_or_none()
        
        if not class_:
            return jsonify({'message': 'Class not found'}), 404
        
        # Cannot leave if leader
        if class_.leader_id == current_user.id:
            return jsonify({'message': 'Class leader cannot leave'}), 400
        
        # Remove membership
        member_result = await session.execute(
            select(ClassMember)
            .where(ClassMember.class_id == class_id)
            .where(ClassMember.user_id == current_user.id)
        )
        member = member_result.scalar_one_or_none()
        
        if not member:
            return jsonify({'message': 'Not a member of this class'}), 400
        
        await session.delete(member)
        await session.commit()
        
        return '', 204
