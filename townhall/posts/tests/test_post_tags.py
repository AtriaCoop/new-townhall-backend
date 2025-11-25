from django.test import TestCase
from django.utils import timezone
from users.models import User
from posts.services import PostServices
from posts.types import CreatePostData, UpdatePostData
from django.core.exceptions import ValidationError


class TestPostTags(TestCase):
    def setUp(self):
        self.regular = User.objects.create(email="user@example.com", is_staff=False)

        self.post_data = CreatePostData(
            content="Hello world!",
            user_id=self.regular.id,
            created_at=timezone.now(),
            tags=["Greeting", "Coding"],
        )

    def testSuccessfulTagCreation(self):
        # Arrange
        post = PostServices.create_post(self.post_data)

        # Act
        saved_tags = list(post.tags.values_list("name", flat=True))

        # Assert
        self.assertCountEqual(saved_tags, ["Greeting", "Coding"])

    def testSuccessfulTagUpdate(self):
        # Arrange
        post = PostServices.create_post(self.post_data)
        update_data = UpdatePostData(
            content="New Hello World!", user_id=self.regular.id, tags=["Test"]
        )

        # Act
        post = PostServices.update_post(1, update_data)
        saved_tags = list(post.tags.values_list("name", flat=True))

        # Assert
        self.assertCountEqual(saved_tags, ["Test"])

    def testEmptyTagCreation(self):
        # Arrange
        empty_tag_data = CreatePostData(
            content="Hello world!",
            user_id=self.regular.id,
            created_at=timezone.now(),
        )

        # Act
        post = PostServices.create_post(empty_tag_data)
        saved_tags = list(post.tags.values_list("name", flat=True))

        # Assert
        self.assertCountEqual(saved_tags, [])

    def testEmptyTagUpdate(self):
        # Arrange
        post = PostServices.create_post(self.post_data)
        update_data = UpdatePostData(
            content="New Hello World!", user_id=self.regular.id, tags=[]
        )

        # Act
        post = PostServices.update_post(1, update_data)
        saved_tags = list(post.tags.values_list("name", flat=True))

        # Assert
        self.assertCountEqual(saved_tags, [])

    def testUnchangedTagUpdate(self):
        # Arrange
        post = PostServices.create_post(self.post_data)
        update_data = UpdatePostData(
            content="New Hello World!", user_id=self.regular.id
        )

        # Act
        post = PostServices.update_post(1, update_data)
        saved_tags = list(post.tags.values_list("name", flat=True))

        # Assert
        self.assertCountEqual(saved_tags, ["Greeting", "Coding"])

    def testTagCreationLimit(self):
        # Arrange
        long_tag = "a" * (PostServices.MAX_TAG_LENGTH + 1)

        tag_limit_data = CreatePostData(
            content="Hello world!",
            user_id=self.regular.id,
            created_at=timezone.now(),
            tags=[long_tag, "Coding"],
        )

        # Act and Assert
        with self.assertRaises(ValidationError) as context:
            PostServices.create_post(tag_limit_data)
        self.assertIn("exceeds", str(context.exception))

    def testTagUpdateLimit(self):
        # Arrange
        long_tag = "a" * (PostServices.MAX_TAG_LENGTH + 1)

        PostServices.create_post(self.post_data)
        update_data = UpdatePostData(
            content="New Hello World!", user_id=self.regular.id, tags=[long_tag]
        )

        # Act and Assert
        with self.assertRaises(ValidationError) as context:
            PostServices.update_post(1, update_data)
        self.assertIn("exceeds", str(context.exception))

    def testTagProfanityCreation(self):
        # Assert
        profanity_tag_data = CreatePostData(
            content="Hello world!",
            user_id=self.regular.id,
            created_at=timezone.now(),
            tags=["Coding", "shit"],
        )

        # Act and Assert
        with self.assertRaises(ValidationError) as context:
            PostServices.create_post(profanity_tag_data)
        self.assertIn("inappropriate language", str(context.exception))

    def testTagProfanityUpdate(self):
        # Arrange
        PostServices.create_post(self.post_data)
        update_data = UpdatePostData(
            content="New Hello World!", user_id=self.regular.id, tags=["bitch"]
        )

        # Act and Assert
        with self.assertRaises(ValidationError) as context:
            PostServices.update_post(1, update_data)
        self.assertIn("inappropriate language", str(context.exception))
