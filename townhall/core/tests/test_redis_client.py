import fakeredis
import time
from django.test import TestCase
from django.forms.models import model_to_dict
from core.cache.redis_client import redis_client
from core.cache.serializers import deserialize_list, serialize_queryset
from users.models import Tag


class TestRedisClient(TestCase):
    def setUp(self):
        # Replace real Redis with fake Redis
        redis_client.client = fakeredis.FakeRedis()

        # Create testing Tag model
        Tag.objects.create(name="Alice")
        Tag.objects.create(name="Bob")
        self.queryset = Tag.objects.all()
        self.serialized = serialize_queryset(self.queryset)

    def test_set_and_get(self):
        # Arrange
        redis_client.set("test_key", self.serialized, 60)

        # Act
        cache_value = redis_client.get("test_key")
        deserialized = deserialize_list(cache_value)

        # Assert
        expected = [model_to_dict(obj) for obj in self.queryset]
        self.assertEqual(deserialized, expected)

    def test_get_missing_key_returns_none(self):
        # Arrange & Act
        value = redis_client.get("missing_key")

        # Assert
        self.assertIsNone(value)

    def test_set_and_get_overwrite(self):
        # Arrange
        redis_client.set("test_key", self.serialized, 60)

        # Act: overwrite with new Tag instances
        Tag.objects.create(name="Charlie")
        queryset_new = Tag.objects.all()
        serialized_new = serialize_queryset(queryset_new)
        redis_client.set("test_key", serialized_new, 60)

        # Retrieve and deserialize
        cache_value = redis_client.get("test_key")
        deserialized = deserialize_list(cache_value)

        # Assert
        expected = [model_to_dict(obj) for obj in queryset_new]
        self.assertEqual(deserialized, expected)

    def test_set_and_get_with_expiration(self):
        # Arrange
        redis_client.set("expiring_key", self.serialized, 1)

        # Act: simulate passage of time to expire the key
        time.sleep(2)
        cache_value = redis_client.get("expiring_key")
        deserialized = deserialize_list(cache_value)

        # Assert
        self.assertEqual(deserialized, [])
