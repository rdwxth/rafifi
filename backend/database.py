from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

class Database:
    def __init__(self):
        self._engine = None
        self._session_factory = None
        
    def init(self, database_url: str):
        """Initialize the database connection"""
        self._engine = create_async_engine(database_url, echo=True)
        self._session_factory = sessionmaker(
            self._engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def session(self):
        """Get a database session"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init() first.")
            
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except:
                await session.rollback()
                raise

# Global database instance
db = Database()
