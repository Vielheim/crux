import asyncio
from sqlalchemy import select
from arq.connections import RedisSettings

from app.database import async_session_factory
from app.models import Climb, ClimbStatus
from app.redis import REDIS_HOST, REDIS_PORT


async def on_startup(ctx):
    print("Worker starting up...")


async def on_shutdown(ctx):
    print("Worker shutting down...")


async def analyze_climb(ctx, climb_id: int, video_url: str):
    """
    Simulates the Computer Vision analysis pipeline.
    1. Fetches Climb record.
    2. Updates status to PROCESSING.
    3. Simulates work (sleep).
    4. Updates status to COMPLETED with dummy results.
    """
    print(f"Starting analysis for Climb ID: {climb_id}")

    async with async_session_factory() as session:
        # 1. Fetch Climb
        stmt = select(Climb).where(Climb.id == climb_id)
        result = await session.execute(stmt)
        climb = result.scalars().first()

        if not climb:
            print(f"Climb {climb_id} not found.")
            return

        # 2. Mark as PROCESSING
        climb.status = ClimbStatus.PROCESSING
        await session.commit()

        # 3. Simulate heavy CV processing (YOLO + MediaPipe)
        # TODO: Replace this sleep with actual pipeline calls
        await asyncio.sleep(5)

        # 4. Mark as COMPLETED & Save Result
        dummy_analysis = {
            "route_detected": True,
            "difficulty_grade": "V5",
            "metrics": {"efficiency": 85, "fluidity": 90},
        }

        climb.analysis_results = dummy_analysis
        climb.status = ClimbStatus.COMPLETED
        await session.commit()

    print(f"Analysis for Climb {climb_id} completed.")


class WorkerSettings:
    """
    Configuration for the Arq Worker.
    """

    on_startup = on_startup
    on_shutdown = on_shutdown
    functions = [analyze_climb]
    redis_settings = RedisSettings(host=REDIS_HOST, port=int(REDIS_PORT))
