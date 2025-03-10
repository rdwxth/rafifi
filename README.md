# Revision App

A comprehensive revision application with flashcards, timetables, and collaborative learning features.

## Features

- User Authentication
  - Registration and login system
  - Password recovery
  - Account settings

- Flashcards
  - Create and manage flashcard sets
  - Assign difficulty levels
  - Study mode with card flipping
  - Test mode with scoring

- Timetable
  - Weekly planning
  - Daily targets (3 on weekdays, 5 on weekends)
  - Progress tracking
  - View previous 4 weeks

- Classes
  - Create and join classes
  - Share resources
  - Class leaderboards
  - Member management

- Progress Tracking
  - XP system
  - Performance analytics
  - Achievement titles
  - Test statistics

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the backend server:
```bash
python backend/app.py
```

3. Start the frontend application:
```bash
python frontend/main.py
```

## Architecture

- Backend: Quart (async Flask-like framework)
- Frontend: Tkinter with CustomTkinter
- Database: SQLite with SQLAlchemy
- Authentication: JWT tokens

## Development

The application is structured as follows:

- `/backend`
  - `app.py` - Main application entry point
  - `models.py` - Database models
  - `/routes` - API endpoints
    - `flashcards.py` - Flashcard management
    - `timetable.py` - Timetable features
    - `classes.py` - Class management

- `/frontend`
  - `main.py` - Main application window
  - `/frames` - UI components
    - `flashcard_frame.py` - Flashcard interface
    - `timetable_frame.py` - Timetable interface
    - `class_frame.py` - Class interface
    - `progress_frame.py` - Progress tracking

## Performance Requirements

- First 10 flashcard sets load within 3 seconds
- Test creation completes in under 5 seconds
- Previous timetables viewable within 4 seconds
- User profiles load within 2 seconds
