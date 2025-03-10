import asyncio
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import (Base, User, FlashcardSet, Flashcard, Test,
                   Timetable, TimetableSlot, Target, Class, ClassMember)

# Create async engine
engine = create_async_engine('sqlite+aiosqlite:///revision_app.db', echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create sample data
    async with async_session() as session:
        # Create sample user
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
        user = User(
            username='student1',
            password=hashed.decode('utf-8'),
            email='student1@example.com',
            xp=100
        )
        session.add(user)
        await session.flush()
        
        # Create sample flashcard sets
        math_set = FlashcardSet(
            name='Math Formulas',
            folder='Mathematics',
            user_id=user.id
        )
        session.add(math_set)
        await session.flush()
        
        # Create sample flashcards
        flashcards = [
            Flashcard(
                front='What is the quadratic formula?',
                back='x = (-b ± √(b² - 4ac)) / 2a',
                difficulty='medium',
                set_id=math_set.id
            ),
            Flashcard(
                front='What is the formula for the area of a circle?',
                back='A = πr²',
                difficulty='easy',
                set_id=math_set.id
            ),
            Flashcard(
                front='What is the Pythagorean theorem?',
                back='a² + b² = c²',
                difficulty='easy',
                set_id=math_set.id
            )
        ]
        for card in flashcards:
            session.add(card)
        
        # Create sample timetable
        timetable = Timetable(
            user_id=user.id,
            week_start=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        session.add(timetable)
        await session.flush()
        
        # Create sample timetable slots
        slots = [
            TimetableSlot(
                timetable_id=timetable.id,
                day=0,  # Monday
                start_time=9*60,  # 9:00 AM
                duration=60,  # 1 hour
                subject='Mathematics'
            ),
            TimetableSlot(
                timetable_id=timetable.id,
                day=2,  # Wednesday
                start_time=14*60,  # 2:00 PM
                duration=90,  # 1.5 hours
                subject='Physics'
            )
        ]
        for slot in slots:
            session.add(slot)
        
        # Create sample targets
        targets = [
            Target(
                timetable_id=timetable.id,
                description='Complete Math chapter 1',
                completed=False
            ),
            Target(
                timetable_id=timetable.id,
                description='Review Physics formulas',
                completed=True
            )
        ]
        for target in targets:
            session.add(target)
        
        # Create sample class
        class_ = Class(
            name='Advanced Mathematics',
            code='MATH101',
            leader_id=user.id
        )
        session.add(class_)
        await session.flush()
        
        # Add user as class member
        member = ClassMember(
            class_id=class_.id,
            user_id=user.id
        )
        session.add(member)
        
        await session.commit()

if __name__ == '__main__':
    print('Initializing database with sample data...')
    asyncio.run(init_db())
    print('Database initialized successfully!')
