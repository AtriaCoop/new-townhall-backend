from .key_builder import build_list_key
from .redis_client import redis_client
from .serializers import serialize_queryset, deserialize_list


class CacheFacade:
    def get_list(self, model, filters: dict, expire_seconds=60):
        """
        Retrieve a list of model instances from Redis cache or store if missing.

        Args:
            model: Django model class to query (e.g., Tag).
            filters: Dictionary of field lookups to filter the queryset.
            expire_seconds: TTL for the cache in seconds (default 60).

        Returns:
            List[dict]: List of model objects represented as dictionaries.
                        Always returns deserialized Python objects, never JSON.
        """

        key = build_list_key(model, filters)

        # 1. Try cache
        cached_data = redis_client.get(key)
        if cached_data:
            return deserialize_list(cached_data)

        # 2. Query DB on cache miss
        queryset = model.objects.filter(**filters)
        data = serialize_queryset(queryset)

        # 3. Write back to cache
        redis_client.set(key, data, expire_seconds)

        return deserialize_list(data)


cache_facade = CacheFacade()
