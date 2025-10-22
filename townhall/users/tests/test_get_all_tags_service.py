from django.test import TestCase
from users.models import Tag
from users.services import UserServices


class GetTagsGivenPrefixTests(TestCase):

    def setUp(self):
        # Create some sample tags in the test database
        Tag.objects.create(name="python")
        Tag.objects.create(name="pytorch")
        Tag.objects.create(name="django")

    def test_get_all_tags(self):
        result = UserServices.get_all_tags()
        self.assertEqual(result, ["python", "pytorch", "django"])

    def test_get_all_tags_empty(self):
        Tag.objects.all().delete()  # clears the table
        result = UserServices.get_all_tags()
        self.assertEqual(result, [])
