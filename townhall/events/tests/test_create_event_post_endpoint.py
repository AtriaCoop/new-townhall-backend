from datetime import date

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event
from posts.models import Post
from users.models import User


class CreateEventPostEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organizer = User.objects.create_user(
            email="organizer@example.com",
            password="test-password",
            full_name="Event Organizer",
            is_staff=True,
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="test-password",
            full_name="Community Member",
        )
        self.event = Event.objects.create(
            title="Community Meetup",
            description="Meet fellow members",
            date=date(2026, 12, 1),
            time="6:00 PM - 8:00 PM",
            location="Town Hall",
            admin=self.organizer,
        )
        self.url = f"/event/{self.event.pk}/create-event-post/"
        self.valid_payload = {"share_to_newsfeed": True}

    def test_create_event_post_success(self):
        self.client.force_authenticate(user=self.organizer)

        response = self.client.post(
            self.url,
            self.valid_payload,
            format="json",
        )

        expected_status = status.HTTP_201_CREATED
        self.assertEqual(response.status_code, expected_status)
        message = response.data["message"]
        event_post_data = response.data["event_post"]
        self.assertEqual(message, "Event post created successfully")
        self.assertEqual(event_post_data["id"], self.event.pk)
        self.assertTrue(event_post_data["hasPost"])

        self.event.refresh_from_db()
        post = self.event.post
        self.assertIsNotNone(post)
        self.assertEqual(post.user, self.organizer)
        self.assertEqual(
            post.content,
            "Join us for the event 'Community Meetup' "
            "on 2026-12-01 at 6:00 PM - 8:00 PM in Town Hall.",
        )
        post_tags = list(post.tags.values_list("name", flat=True))
        self.assertEqual(post_tags, ["event"])

    def test_create_event_post_requires_authentication(self):
        response = self.client.post(
            self.url,
            self.valid_payload,
            format="json",
        )

        expected_status = status.HTTP_401_UNAUTHORIZED
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response.data["error"], "Not authenticated")
        self.assertFalse(Post.objects.exists())

    def test_create_event_post_requires_organizer(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            self.url,
            self.valid_payload,
            format="json",
        )

        expected_status = status.HTTP_403_FORBIDDEN
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(
            response.data["error"],
            "Only organizers can create event posts",
        )
        self.assertFalse(Post.objects.exists())

    def test_create_event_post_rejects_missing_share_flag(self):
        self.client.force_authenticate(user=self.organizer)

        response = self.client.post(self.url, {}, format="json")

        expected_status = status.HTTP_400_BAD_REQUEST
        self.assertEqual(response.status_code, expected_status)
        self.assertIn("share_to_newsfeed", response.data)
        self.assertFalse(Post.objects.exists())

    def test_create_event_post_returns_error_for_missing_event(self):
        self.client.force_authenticate(user=self.organizer)

        response = self.client.post(
            "/event/99999/create-event-post/",
            self.valid_payload,
            format="json",
        )

        expected_status = status.HTTP_400_BAD_REQUEST
        self.assertEqual(response.status_code, expected_status)
        error = response.data["error"]
        self.assertIn("Event with id 99999 does not exist.", error)
        self.assertFalse(Post.objects.exists())

    def test_create_event_post_rejects_duplicate_post(self):
        self.client.force_authenticate(user=self.organizer)
        existing_post = Post.objects.create(
            user=self.organizer,
            content="Already shared",
        )
        self.event.post = existing_post
        self.event.save()

        response = self.client.post(
            self.url,
            self.valid_payload,
            format="json",
        )

        expected_status = status.HTTP_400_BAD_REQUEST
        self.assertEqual(response.status_code, expected_status)
        error = response.data["error"]
        self.assertIn("Event post already exists.", error)
        self.assertEqual(Post.objects.count(), 1)
