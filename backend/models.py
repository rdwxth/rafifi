from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, LargeBinary
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(LargeBinary, nullable=False)  # Store password as bytes
    email = Column(String(100), unique=True, nullable=False)
    recovery_email = Column(String(100))
    xp = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    flashcard_sets = relationship('FlashcardSet', back_populates='user', cascade='all, delete-orphan')
    tests = relationship('Test', back_populates='user', cascade='all, delete-orphan')
    timetables = relationship('Timetable', back_populates='user', cascade='all, delete-orphan')
    titles = relationship('UserTitle', back_populates='user', cascade='all, delete-orphan')
    class_memberships = relationship('ClassMember', back_populates='user', cascade='all, delete-orphan')

class FlashcardSet(Base):
    __tablename__ = 'flashcard_sets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    folder = Column(String(100))
    priority = Column(Integer, default=1)
    hash_key = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='flashcard_sets')
    flashcards = relationship('Flashcard', back_populates='flashcard_set', cascade='all, delete-orphan')

class Flashcard(Base):
    __tablename__ = 'flashcards'
    
    id = Column(Integer, primary_key=True)
    set_id = Column(Integer, ForeignKey('flashcard_sets.id'), nullable=False)
    front = Column(String(1000), nullable=False)
    back = Column(String(1000), nullable=False)
    priority = Column(Integer, default=1)
    hash_key = Column(String(64), nullable=False)
    incorrect_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime)
    
    # Relationships
    flashcard_set = relationship('FlashcardSet', back_populates='flashcards')

class Test(Base):
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='tests')
    questions = relationship('TestQuestion', back_populates='test', cascade='all, delete-orphan')
    results = relationship('TestResult', back_populates='test', cascade='all, delete-orphan')

class TestQuestion(Base):
    __tablename__ = 'test_questions'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    flashcard_id = Column(Integer, ForeignKey('flashcards.id'), nullable=False)
    order = Column(Integer, nullable=False)
    correct = Column(Boolean)
    
    # Relationships
    test = relationship('Test', back_populates='questions')
    flashcard = relationship('Flashcard')

class TestResult(Base):
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    score = Column(Float, nullable=False)
    duration = Column(Integer)  # in seconds
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test = relationship('Test', back_populates='results')
    user = relationship('User')

class Timetable(Base):
    __tablename__ = 'timetables'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    week_start = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='timetables')
    targets = relationship('Target', back_populates='timetable', cascade='all, delete-orphan')

class Target(Base):
    __tablename__ = 'targets'
    
    id = Column(Integer, primary_key=True)
    timetable_id = Column(Integer, ForeignKey('timetables.id'), nullable=False)
    day = Column(Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    description = Column(String(200), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # Relationships
    timetable = relationship('Timetable', back_populates='targets')

class UserTitle(Base):
    __tablename__ = 'user_titles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(50), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='titles')

class Class(Base):
    __tablename__ = 'classes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    leader_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    leader = relationship('User', backref='classes_led')
    members = relationship('ClassMember', back_populates='class_')
    leaderboards = relationship('Leaderboard', back_populates='class_')

class ClassMember(Base):
    __tablename__ = 'class_members'
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    class_ = relationship('Class', back_populates='members')
    user = relationship('User', back_populates='class_memberships')

class Leaderboard(Base):
    __tablename__ = 'leaderboards'
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    class_ = relationship('Class', back_populates='leaderboards')
