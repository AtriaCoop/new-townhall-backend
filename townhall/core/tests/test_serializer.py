from django.test import TestCase
from core.cache.serializers import serialize_queryset, deserialize_list
from users.models import Tag


class TestSerializer(TestCase):
    def test_serializer_deserializer_with_model(db):
        Tag.objects.create(name="Alice")
        Tag.objects.create(name="Bob")

        qs = Tag.objects.all()

        json_str = serialize_queryset(qs)
        data = deserialize_list(json_str)

        assert len(data) == 2
        assert data[0]["name"] == "Alice"

    def test_deserialize_none_returns_empty_list(self):
        # Arrange
        json_str = None

        # Act
        result = deserialize_list(json_str)

        # Assert
        self.assertEqual(result, [])
