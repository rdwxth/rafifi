from quart import Blueprint, request, jsonify
from sqlalchemy import select
from models import Timetable, Target
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
                .order_by(Target.day, Target.id)
            )
            targets = targets_result.scalars().all()
            
            # Group targets by day
            targets_by_day = {}
            for target in targets:
                if target.day not in targets_by_day:
                    targets_by_day[target.day] = []
                targets_by_day[target.day].append({
                    'id': target.id,
                    'description': target.description,
                    'completed': target.completed,
                    'completed_at': target.completed_at.isoformat() if target.completed_at else None
                })
            
            response.append({
                'id': timetable.id,
                'week_start': timetable.week_start.isoformat(),
                'targets': targets_by_day
            })
        
        return jsonify(response)

@timetable_bp.route('/', methods=['POST'])
@token_required
async def create_timetable(current_user):
    data = await request.get_json()
    
    if 'week_start' not in data or 'targets' not in data:
        return jsonify({'message': 'Missing required fields'}), 400
    
    week_start = datetime.fromisoformat(data['week_start'])
    targets_by_day = data['targets']
    
    # Validate target limits
    for day, targets in targets_by_day.items():
        day = int(day)
        max_targets = 5 if day >= 5 else 3  # 5 for weekends, 3 for weekdays
        if len(targets) > max_targets:
            return jsonify({
                'message': f'Maximum {max_targets} targets allowed for day {day}'
            }), 400
    
    async with async_session() as session:
        # Check if timetable already exists for this week
        result = await session.execute(
            select(Timetable)
            .where(Timetable.user_id == current_user.id)
            .where(Timetable.week_start == week_start)
        )
        if result.scalar_one_or_none():
            return jsonify({'message': 'Timetable already exists for this week'}), 400
        
        # Create new timetable
        new_timetable = Timetable(
            user_id=current_user.id,
            week_start=week_start
        )
        session.add(new_timetable)
        await session.flush()  # Get timetable ID
        
        # Create targets
        targets_data = []
        for day, targets in targets_by_day.items():
            for description in targets:
                target = Target(
                    timetable_id=new_timetable.id,
                    day=int(day),
                    description=description,
                    completed=False
                )
                session.add(target)
                targets_data.append({
                    'day': int(day),
                    'description': description,
                    'completed': False
                })
        
        await session.commit()
        
        return jsonify({
            'id': new_timetable.id,
            'week_start': new_timetable.week_start.isoformat(),
            'targets': targets_data
        }), 201

@timetable_bp.route('/current', methods=['GET'])
@token_required
async def get_current_timetable(current_user):
    async with async_session() as session:
        # Get current week's Monday
        today = datetime.now()
        current_week_start = today - timedelta(days=today.weekday())
        current_week_start = current_week_start.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Get timetable for current week
        result = await session.execute(
            select(Timetable)
            .where(Timetable.user_id == current_user.id)
            .where(Timetable.week_start == current_week_start)
        )
        timetable = result.scalar_one_or_none()
        
        if not timetable:
            return jsonify({'message': 'No timetable found for current week'}), 404
            
        # Get all targets for this timetable
        result = await session.execute(
            select(Target)
            .where(Target.timetable_id == timetable.id)
            .order_by(Target.day, Target.id)
        )
        targets = result.scalars().all()
        
        # Group targets by day
        targets_by_day = {}
        for target in targets:
            if target.day not in targets_by_day:
                targets_by_day[target.day] = []
            targets_by_day[target.day].append({
                'id': target.id,
                'description': target.description,
                'completed': target.completed,
                'completed_at': target.completed_at.isoformat() if target.completed_at else None
            })
            
        return jsonify({
            'id': timetable.id,
            'week_start': timetable.week_start.isoformat(),
            'targets': targets_by_day
        })

@timetable_bp.route('/history', methods=['GET'])
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
        
        response = []
        for timetable in timetables:
            # Get targets for this timetable
            targets_result = await session.execute(
                select(Target)
                .where(Target.timetable_id == timetable.id)
                .order_by(Target.day, Target.id)
            )
            targets = targets_result.scalars().all()
            
            # Calculate completion rate
            total_targets = len(targets)
            completed_targets = sum(1 for t in targets if t.completed)
            completion_rate = completed_targets / total_targets if total_targets > 0 else 0
            
            response.append({
                'id': timetable.id,
                'week_start': timetable.week_start.isoformat(),
                'total_targets': total_targets,
                'completed_targets': completed_targets,
                'completion_rate': completion_rate
            })
        
        return jsonify(response)

@timetable_bp.route('/target/<int:target_id>/complete', methods=['POST'])
@token_required
async def complete_target(current_user, target_id):
    async with async_session() as session:
        # Get target and verify ownership
        result = await session.execute(
            select(Target)
            .join(Timetable)
            .where(Target.id == target_id)
            .where(Timetable.user_id == current_user.id)
        )
        target = result.scalar_one_or_none()
        
        if not target:
            return jsonify({'message': 'Target not found'}), 404
        
        # Complete target
        target.completed = True
        target.completed_at = datetime.utcnow()
        
        # Calculate XP gained (more XP for completing targets on time)
        today = datetime.now()
        target_day = target.timetable.week_start + timedelta(days=target.day)
        xp_gained = 50 if today.date() <= target_day.date() else 25
        
        await session.commit()
        
        return jsonify({
            'message': 'Target completed successfully',
            'xp_gained': xp_gained
        })
