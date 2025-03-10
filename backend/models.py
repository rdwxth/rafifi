from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    recovery_email = Column(String(120))
    xp = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    flashcard_sets = relationship('FlashcardSet', back_populates='user')
    timetables = relationship('Timetable', back_populates='user')
    class_memberships = relationship('ClassMember', back_populates='user')
    tests = relationship('Test', back_populates='user')

class FlashcardSet(Base):
    __tablename__ = 'flashcard_sets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    folder = Column(String(50), default='General')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='flashcard_sets')
    flashcards = relationship('Flashcard', back_populates='set', cascade='all, delete-orphan')
    tests = relationship('Test', back_populates='flashcard_set')

class Flashcard(Base):
    __tablename__ = 'flashcards'
    
    id = Column(Integer, primary_key=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    difficulty = Column(String(20), default='medium')  # easy, medium, hard
    set_id = Column(Integer, ForeignKey('flashcard_sets.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    set = relationship('FlashcardSet', back_populates='flashcards')

class Test(Base):
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    flashcard_set_id = Column(Integer, ForeignKey('flashcard_sets.id'), nullable=False)
    score = Column(Float, nullable=False)
    duration = Column(Integer)  # in seconds
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='tests')
    flashcard_set = relationship('FlashcardSet', back_populates='tests')

class Timetable(Base):
    __tablename__ = 'timetables'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    week_start = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='timetables')
    slots = relationship('TimetableSlot', back_populates='timetable', cascade='all, delete-orphan')
    targets = relationship('Target', back_populates='timetable', cascade='all, delete-orphan')

class TimetableSlot(Base):
    __tablename__ = 'timetable_slots'
    
    id = Column(Integer, primary_key=True)
    timetable_id = Column(Integer, ForeignKey('timetables.id'), nullable=False)
    day = Column(Integer, nullable=False)  # 0-6 for Monday-Sunday
    start_time = Column(Integer, nullable=False)  # minutes from midnight
    duration = Column(Integer, nullable=False)  # in minutes
    subject = Column(String(100), nullable=False)
    
    timetable = relationship('Timetable', back_populates='slots')

class Target(Base):
    __tablename__ = 'targets'
    
    id = Column(Integer, primary_key=True)
    timetable_id = Column(Integer, ForeignKey('timetables.id'), nullable=False)
    description = Column(String(255), nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    timetable = relationship('Timetable', back_populates='targets')

class Class(Base):
    __tablename__ = 'classes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    leader_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    members = relationship('ClassMember', back_populates='class_')
    leaderboards = relationship('Leaderboard', back_populates='class_')

class ClassMember(Base):
    __tablename__ = 'class_members'
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    class_ = relationship('Class', back_populates='members')
    user = relationship('User', back_populates='class_memberships')

class Leaderboard(Base):
    __tablename__ = 'leaderboards'
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    class_ = relationship('Class', back_populates='leaderboards')
