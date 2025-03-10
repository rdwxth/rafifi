from sqlalchemy import create_engine
from sqlalchemy.sql import text
from datetime import datetime, timedelta
import bcrypt
import hashlib
import os

# Import models
from models import (Base, User, FlashcardSet, Flashcard, Test,
                   TestQuestion, TestResult, Timetable, Target, UserTitle)

def generate_hash_key(prefix, *args):
    """Generate a hash key for database objects"""
    timestamp = datetime.utcnow().timestamp()
    data = f"{prefix}:{':'.join(str(arg) for arg in args)}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()

def init_db():
    # Use relative path from current directory
    engine = create_engine('sqlite:///database/rafifi.db')
    Base.metadata.drop_all(engine)  # Drop all tables first
    Base.metadata.create_all(engine)
    
    # Create sample data
    with engine.connect() as conn:
        # Create sample user
        password = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
        conn.execute(
            User.__table__.insert(),
            {
                'username': 'student1',
                'password': password,
                'email': 'student1@example.com',
                'xp': 0,
                'created_at': datetime.utcnow()
            }
        )
        conn.commit()
        
        # Get the user's ID
        result = conn.execute(text("SELECT id FROM users WHERE username = 'student1'"))
        user_id = result.scalar()
        
        # Add initial title
        conn.execute(
            UserTitle.__table__.insert(),
            {
                'user_id': user_id,
                'title': 'Beginner',
                'earned_at': datetime.utcnow()
            }
        )
        
        # Create sample flashcard set
        set_hash = generate_hash_key('set', user_id, 'Sample Set')
        conn.execute(
            FlashcardSet.__table__.insert(),
            {
                'user_id': user_id,
                'name': 'Sample Set',
                'description': 'A sample flashcard set',
                'folder': 'General',
                'priority': 1,
                'hash_key': set_hash,
                'created_at': datetime.utcnow()
            }
        )
        
        # Get the set's ID
        result = conn.execute(text("SELECT id FROM flashcard_sets WHERE user_id = :user_id"), {'user_id': user_id})
        set_id = result.scalar()
        
        # Create sample flashcards
        conn.execute(
            Flashcard.__table__.insert(),
            [
                {
                    'set_id': set_id,
                    'front': 'What is a Priority Queue?',
                    'back': 'A data structure where elements have priorities and higher priority elements are served first',
                    'priority': 3,
                    'hash_key': generate_hash_key('card', set_id, 'Priority Queue'),
                    'incorrect_count': 0,
                    'last_reviewed': datetime.utcnow() - timedelta(days=7)
                },
                {
                    'set_id': set_id,
                    'front': 'What is Merge Sort?',
                    'back': 'A divide-and-conquer sorting algorithm with O(n log n) time complexity',
                    'priority': 2,
                    'hash_key': generate_hash_key('card', set_id, 'Merge Sort'),
                    'incorrect_count': 0,
                    'last_reviewed': datetime.utcnow() - timedelta(days=3)
                }
            ]
        )
        
        # Create sample test
        conn.execute(
            Test.__table__.insert(),
            {
                'user_id': user_id,
                'name': 'Sample Test',
                'description': 'A sample test',
                'created_at': datetime.utcnow()
            }
        )
        
        # Get the test's ID
        result = conn.execute(text("SELECT id FROM tests WHERE user_id = :user_id"), {'user_id': user_id})
        test_id = result.scalar()
        
        # Get flashcard IDs
        result = conn.execute(text("SELECT id FROM flashcards WHERE set_id = :set_id"), {'set_id': set_id})
        flashcard_ids = [row[0] for row in result]
        
        # Create sample test questions
        conn.execute(
            TestQuestion.__table__.insert(),
            [
                {
                    'test_id': test_id,
                    'flashcard_id': flashcard_ids[0],
                    'order': 1,
                    'correct': None
                },
                {
                    'test_id': test_id,
                    'flashcard_id': flashcard_ids[1],
                    'order': 2,
                    'correct': None
                }
            ]
        )
        
        # Create sample timetable
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        conn.execute(
            Timetable.__table__.insert(),
            {
                'user_id': user_id,
                'week_start': monday,
                'created_at': datetime.utcnow()
            }
        )
        
        # Get the timetable's ID
        result = conn.execute(text("SELECT id FROM timetables WHERE user_id = :user_id"), {'user_id': user_id})
        timetable_id = result.scalar()
        
        # Create sample targets
        conn.execute(
            Target.__table__.insert(),
            [
                {
                    'timetable_id': timetable_id,
                    'day': 0,  # Monday
                    'description': 'Review Priority Queues',
                    'completed': False
                },
                {
                    'timetable_id': timetable_id,
                    'day': 1,  # Tuesday
                    'description': 'Practice Merge Sort',
                    'completed': False
                }
            ]
        )
        
        conn.commit()

if __name__ == '__main__':
    init_db()
