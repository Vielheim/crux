import os
from arq import create_pool
from arq.connections import RedisSettings

# Load config
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")


async def get_redis_pool():
    """
    Creates and returns an Arq Redis pool.
    """
    return await create_pool(RedisSettings(host=REDIS_HOST, port=int(REDIS_PORT)))
