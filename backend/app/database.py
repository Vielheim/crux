import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Load the connection string from the environment
# This matches the variable we set in docker-compose/env file
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Check your .env file.")

# Create the Async Engine
# echo=True logs all SQL queries to the console (great for debugging dev)
engine = create_async_engine(DATABASE_URL, echo=True)

# Create the Session Factory
# This is what we call to get a fresh database session for each request
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Define the Base class
# All our models (User, Climb) will inherit from this
class Base(DeclarativeBase):
    pass


# Dependency for FastAPI
# Returns a generator that yields a new database session
# It is managed by a context manager to ensure proper cleanup
# Once the session execution is complete, the session is closed automatically
# usage: def my_endpoint(db: AsyncSession = Depends(get_db)):
async def get_db():
    async with async_session_factory() as session:
        yield session
