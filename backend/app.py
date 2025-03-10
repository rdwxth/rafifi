from quart import Quart
from quart_cors import cors
from routes.auth import auth_bp
from routes.timetable import timetable_bp
from routes.flashcards import flashcard_bp
from models import Base
from sqlalchemy.ext.asyncio import create_async_engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)
app = cors(app, allow_origin="*")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(timetable_bp, url_prefix='/timetable')
app.register_blueprint(flashcard_bp, url_prefix='/flashcard')  # Match frontend URL

# Use database path relative to current directory
engine = create_async_engine('sqlite+aiosqlite:///database/rafifi.db', echo=True)

@app.before_serving
async def startup():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
