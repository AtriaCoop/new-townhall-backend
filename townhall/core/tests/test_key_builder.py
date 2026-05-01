from django.test import TestCase
from core.cache.key_builder import build_list_key
from users.models import Tag


class TestKeyBuilder(TestCase):
    def test_build_key_with_filters(self):
        # Arrange
        filters = {"name": "Alice"}

        # Act
        key = build_list_key(Tag, filters)

        # Assert
        self.assertEqual(key, "list:Tag:name=Alice")

    def test_build_key_with_unsorted_filters(self):
        # Arrange
        filters = {"name": "Alice", "id": 5}

        # Act
        key = build_list_key(Tag, filters)

        # Assert
        self.assertEqual(key, "list:Tag:id=5&name=Alice")

    def test_build_key_with_empty_filters(self):
        # Arrange
        filters = {}

        # Act
        key = build_list_key(Tag, filters)

        # Assert
        self.assertEqual(key, "list:Tag:all")

    def test_build_key_consistency(self):
        # Arrange
        filters1 = {"name": "Alice", "id": 5}
        filters2 = {"id": 5, "name": "Alice"}

        # Act
        key1 = build_list_key(Tag, filters1)
        key2 = build_list_key(Tag, filters2)

        # Assert
        self.assertEqual(key1, key2)
