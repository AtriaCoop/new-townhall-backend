import fakeredis
from django.test import TestCase
from django.forms.models import model_to_dict
from core.cache.redis_client import redis_client
from core.cache.cache_facade import cache_facade
from core.cache.serializers import serialize_queryset, deserialize_list
from users.models import Tag


class TestCacheFacade(TestCase):

    def setUp(self):
        # Set up fake Redis server for testing
        redis_client.client = fakeredis.FakeRedis()

        # Create test data
        Tag.objects.create(name="Alice")
        Tag.objects.create(name="Bob")

        self.filters = {"name": "Alice"}

    def test_cache_miss_fetches_from_db(self):
        # Arrange
        key = "list:Tag:name=Alice"  # expected Redis key

        # Make sure cache is empty
        self.assertIsNone(redis_client.get(key))

        # Act
        result = cache_facade.get_list(Tag, self.filters)

        # Assert
        expected_queryset = Tag.objects.filter(**self.filters)
        expected_list_of_dicts = [model_to_dict(obj) for obj in expected_queryset]
        self.assertEqual(result, expected_list_of_dicts)

        # Confirm it was written to cache
        cached_value = redis_client.get(key)
        cached_list = deserialize_list(cached_value)
        self.assertEqual(cached_list, expected_list_of_dicts)

    def test_cache_hit_returns_cached_data(self):
        # Arrange
        key = "list:Tag:name=Alice"
        queryset = Tag.objects.filter(**self.filters)
        serialized = serialize_queryset(queryset)

        # Pre-populate Redis with serialized data
        redis_client.set(key, serialized, 60)

        # Act
        result = cache_facade.get_list(Tag, self.filters)

        # Assert: returned value matches deserialized cached data
        expected_list = deserialize_list(serialized)
        self.assertEqual(result, expected_list)

    def test_empty_queryset_returns_empty_list(self):
        # Arrange
        filters = {"name": "Charlie"}
        key = "list:Tag:name=Charlie"

        # Act
        result = cache_facade.get_list(Tag, filters)

        # Assert
        self.assertEqual(result, [])

        # Confirm that Redis stores empty list as JSON
        cached_value = redis_client.get(key)
        cached_list = deserialize_list(cached_value)
        self.assertEqual(cached_list, [])
