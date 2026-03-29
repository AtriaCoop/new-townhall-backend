from django.test import TestCase
from django.core.cache import cache

from core.cache.cache_facade import cache_facade
from users.models import Tag


class TestCacheFacade(TestCase):

    def setUp(self):
        cache.clear()

        Tag.objects.create(name="Alice")
        Tag.objects.create(name="Bob")

        self.filters = {"name": "Alice"}

    def test_cache_miss_fetches_from_db(self):
        key = "list:Tag:name=Alice"

        self.assertIsNone(cache.get(key))

        result = cache_facade.get_list(Tag, self.filters)

        expected_queryset = Tag.objects.filter(**self.filters)
        expected_list = list(expected_queryset.values())

        self.assertEqual(result, expected_list)

        cached_value = cache.get(key)
        self.assertEqual(cached_value, expected_list)

    def test_cache_hit_returns_cached_data(self):
        key = "list:Tag:name=Alice"

        queryset = Tag.objects.filter(**self.filters)
        expected_list = list(queryset.values())

        cache.set(key, expected_list, 60)

        result = cache_facade.get_list(Tag, self.filters)

        self.assertEqual(result, expected_list)

    def test_empty_queryset_returns_empty_list(self):
        filters = {"name": "Charlie"}
        key = "list:Tag:name=Charlie"

        result = cache_facade.get_list(Tag, filters)

        self.assertEqual(result, [])

        cached_value = cache.get(key)
        self.assertEqual(cached_value, [])

    def test_cache_hit_avoids_db_query(self):
        key = "list:Tag:name=Alice"

        expected_list = [{"id": 999, "name": "Fake"}]
        cache.set(key, expected_list, 60)

        result = cache_facade.get_list(Tag, self.filters)

        self.assertEqual(result, expected_list)
