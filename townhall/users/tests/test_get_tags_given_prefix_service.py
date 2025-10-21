from django.test import TestCase
from users.models import Tag
from users.services import UserServices


class GetTagsGivenPrefixTests(TestCase):

    def setUp(self):
        # Create some sample tags in the test database
        Tag.objects.create(name="python")
        Tag.objects.create(name="pytorch")
        Tag.objects.create(name="django")

    def test_returns_tags_matching_prefix(self):
        result = UserServices.get_tags_given_prefix("py")
        self.assertEqual(result, ["python", "pytorch"])

    def test_returns_empty_list_for_no_matches(self):
        result = UserServices.get_tags_given_prefix("zzz")
        self.assertEqual(result, [])

    def test_case_insensitive(self):
        result = UserServices.get_tags_given_prefix("PY")
        self.assertEqual(result, ["python", "pytorch"])
