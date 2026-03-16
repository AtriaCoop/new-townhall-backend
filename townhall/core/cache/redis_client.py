import redis
import os


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
        )

    def get(self, key):
        raw = self.client.get(key)
        return raw.decode("utf-8") if raw else None

    def set(self, key, value, expire_seconds):
        self.client.set(key, value, ex=expire_seconds)


redis_client = RedisClient()
