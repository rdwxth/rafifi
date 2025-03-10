from quart import Blueprint, request, jsonify
from sqlalchemy import select
from models import Timetable, TimetableSlot, Target
from utils import token_required, async_session
from datetime import datetime, timedelta

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/', methods=['GET'])
@token_required
async def get_timetables(current_user):
    async with async_session() as session:
        result = await session.execute(
            select(Timetable)
            .where(Timetable.user_id == current_user.id)
            .order_by(Timetable.week_start.desc())
            .limit(4)  # Last 4 weeks
        )
        timetables = result.scalars().all()
        
        response = []
        for timetable in timetables:
            targets_result = await session.execute(
                select(Target)
                .where(Target.timetable_id == timetable.id)
                .order_by(Target.id)
            )
            targets = targets_result.scalars().all()
            
            response.append({
                'id': timetable.id,
                'week_start': timetable.week_start.isoformat(),
                'targets': [{
                    'id': t.id,
                    'description': t.description,
                    'completed': t.completed
                } for t in targets]
            })
        
        return jsonify(response)

@timetable_bp.route('/', methods=['POST'])
@token_required
async def create_timetable(current_user):
    data = await request.get_json()
    
    if 'week_start' not in data:
        # If week_start not provided, use current week's Monday
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
    else:
        week_start = datetime.fromisoformat(data['week_start'])
    
    async with async_session() as session:
        # Check if timetable already exists for this week
        result = await session.execute(
            select(Timetable)
            .where(Timetable.user_id == current_user.id)
            .where(Timetable.week_start == week_start)
        )
        if result.scalar_one_or_none():
            return jsonify({'message': 'Timetable already exists for this week'}), 400
        
        new_timetable = Timetable(
            user_id=current_user.id,
            week_start=week_start
        )
        session.add(new_timetable)
        await session.commit()
        
        return jsonify({
            'id': new_timetable.id,
            'week_start': new_timetable.week_start.isoformat(),
            'targets': []
        }), 201

@timetable_bp.route('/<int:timetable_id>/targets', methods=['POST'])
@token_required
async def add_target(current_user, timetable_id):
    data = await request.get_json()
    
    if not all(k in data for k in ['description']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    async with async_session() as session:
        # Verify timetable ownership
        result = await session.execute(
            select(Timetable)
            .where(Timetable.id == timetable_id)
            .where(Timetable.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            return jsonify({'message': 'Timetable not found'}), 404
        
        new_target = Target(
            timetable_id=timetable_id,
            description=data['description'],
            completed=False
        )
        session.add(new_target)
        await session.commit()
        
        return jsonify({
            'id': new_target.id,
            'description': new_target.description,
            'completed': new_target.completed
        }), 201

@timetable_bp.route('/<int:timetable_id>/targets/<int:target_id>', methods=['PUT'])
@token_required
async def update_target(current_user, timetable_id, target_id):
    data = await request.get_json()
    
    async with async_session() as session:
        # Verify timetable ownership
        timetable_result = await session.execute(
            select(Timetable)
            .where(Timetable.id == timetable_id)
            .where(Timetable.user_id == current_user.id)
        )
        if not timetable_result.scalar_one_or_none():
            return jsonify({'message': 'Timetable not found'}), 404
        
        # Get target
        target_result = await session.execute(
            select(Target)
            .where(Target.id == target_id)
            .where(Target.timetable_id == timetable_id)
        )
        target = target_result.scalar_one_or_none()
        
        if not target:
            return jsonify({'message': 'Target not found'}), 404
        
        # Update fields
        if 'description' in data:
            target.description = data['description']
        if 'completed' in data:
            target.completed = data['completed']
        
        await session.commit()
        
        return jsonify({
            'id': target.id,
            'description': target.description,
            'completed': target.completed
        })

@timetable_bp.route('/timetable/current', methods=['GET'])
@token_required
async def get_current_timetable(current_user):
    async with async_session() as session:
        # Get the most recent timetable
        result = await session.execute(
            select(Timetable)
            .where(Timetable.user_id == current_user.id)
            .order_by(Timetable.week_start.desc())
            .limit(1)
        )
        timetable = result.scalar_one_or_none()
        
        if not timetable:
            return jsonify({'message': 'No timetable found'}), 404
            
        # Get all targets for this timetable
        result = await session.execute(
            select(Target)
            .where(Target.timetable_id == timetable.id)
            .order_by(Target.id)
        )
        targets = result.scalars().all()
        
        targets_by_day = {}
        for target in targets:
            if target.id not in targets_by_day:
                targets_by_day[target.id] = []
            targets_by_day[target.id].append({
                'id': target.id,
                'description': target.description,
                'completed': target.completed
            })
            
        return jsonify({
            'week_start': timetable.week_start.isoformat(),
            'targets': targets_by_day
        })

@timetable_bp.route('/timetable/history', methods=['GET'])
@token_required
async def get_timetable_history(current_user):
    async with async_session() as session:
        # Get last 4 timetables
        result = await session.execute(
            select(Timetable)
            .where(Timetable.user_id == current_user.id)
            .order_by(Timetable.week_start.desc())
            .limit(4)
        )
        timetables = result.scalars().all()
        
        timetable_data = []
        for timetable in timetables:
            result = await session.execute(
                select(Target)
                .where(Target.timetable_id == timetable.id)
            )
            targets = result.scalars().all()
            
            completed_targets = sum(1 for t in targets if t.completed)
            total_targets = len(targets)
            
            timetable_data.append({
                'week_start': timetable.week_start.isoformat(),
                'completed_targets': completed_targets,
                'total_targets': total_targets,
                'completion_rate': completed_targets / total_targets if total_targets > 0 else 0
            })
            
        return jsonify(timetable_data)

@timetable_bp.route('/timetable/target/<int:target_id>/complete', methods=['POST'])
@token_required
async def complete_target(current_user, target_id):
    async with async_session() as session:
        target = await session.get(Target, target_id)
        
        if not target:
            return jsonify({'message': 'Target not found'}), 404
            
        # Verify target belongs to user's timetable
        timetable = await session.get(Timetable, target.timetable_id)
        if timetable.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        target.completed = True
        await session.commit()
        
        # Award XP for completing target
        current_user.xp += 10
        await session.commit()
        
        return jsonify({
            'message': 'Target completed successfully',
            'xp_gained': 10
        })
