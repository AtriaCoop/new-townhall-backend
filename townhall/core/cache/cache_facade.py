from django.core.cache import cache
from .key_builder import build_list_key


class CacheFacade:
    def get_list(self, model, filters: dict, timeout=60):
        """
        Retrieve a list of model instances from Redis cache or store if missing.

        Args:
            model: Django model class to query (e.g., Tag).
            filters: Dictionary of field lookups to filter the queryset.
            timeout: TTL for the cache in seconds (default 60).

        Returns:
            List[dict]: List of model objects represented as dictionaries.
                        Always returns deserialized Python objects, never JSON.
        """

        key = build_list_key(model, filters)

        # 1. Try cache
        cached_data = cache.get(key)
        if cached_data is not None:
            return cached_data

        # 2. Query DB on cache miss
        queryset = model.objects.filter(**filters)
        data = list(queryset.values())

        # 3. Write back to cache
        cache.set(key, data, timeout)

        return data


cache_facade = CacheFacade()
