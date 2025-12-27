import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import get_db, Base

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
)

TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    # Asyncio requires an event loop per thread
    # Sometimes, defining a session-scoped loop helps avoid
    # "Event loop is closed" errors when sharing resources
    # like the database engine across multiple tests.
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Creates a fresh database session for a test.
    Creates tables before the test and drops them after.
    """
    # Create the database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide a session to the test
    async with TestingSessionLocal() as session:
        yield session

    # Drop the database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """
    Dependency Override: Forces the app to use our test DB session
    instead of the real Postgres connection.
    """

    async def override_get_db():
        yield db_session

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create the client and run the test
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    # Clear the overrides after the test
    app.dependency_overrides.clear()
