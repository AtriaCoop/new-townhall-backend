from django.test import TestCase
from django.core.management import call_command
from users.services import UserServices


class TestSearchUsersService(TestCase):

    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)

    def test_search_users_test_match(self):

        # Arrange
        test_data = "Bob"

        # Act
        search_results = UserServices.search_users_for_mention(test_data)

        # Assert
        self.assertEqual(search_results.first().pk, 1)

    def test_search_users_no_match(self):

        # Arrange
        test_data = "Zzzzz"

        # Act
        search_results = UserServices.search_users_for_mention(test_data)

        # Assert
        self.assertEqual(search_results.count(), 0)

    def test_search_users_no_input(self):

        # Arrange
        test_data = ""

        # Act
        search_results = UserServices.search_users_for_mention(test_data)

        # Assert
        self.assertEqual(search_results.count(), 0)

    def test_search_users_invalid_input(self):

        # Arrange
        test_data = 123

        # Act
        search_results = UserServices.search_users_for_mention(test_data)

        # Assert
        self.assertEqual(search_results.count(), 0)
