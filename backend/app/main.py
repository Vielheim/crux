import random
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import our database session dependency and the User model
from app.database import get_db
from app.models import User

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Crux Backend is running!"}


# TEST ENDPOINT 1: WRITE
# Creates a random user every time you hit it
@app.post("/test/user")
async def test_create_user(db: AsyncSession = Depends(get_db)):
    # Generate a random suffix to avoid "Unique Constraint" errors on re-runs
    suffix = random.randint(1000, 9999)

    new_user = User(username=f"climber_{suffix}", email=f"climber_{suffix}@crux.com")

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)  # Reloads the object with the ID assigned by DB

    return {"status": "success", "created_user": new_user}


# TEST ENDPOINT 2: READ
# Fetches all users from the DB
@app.get("/test/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    # "select(User)" is the standard SQLAlchemy 2.0 syntax
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
