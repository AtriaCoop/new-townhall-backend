import json

from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from posts.models import Post
from posts.serializers import PostSerializer
from posts.views import _validate_gif
from users.models import User

GIF = {
    "provider": "giphy",
    "id": "abc123",
    "title": "Happy Cat",
    "video_url": "https://media2.giphy.com/media/abc123/giphy.mp4",
    "preview_url": "https://media2.giphy.com/media/abc123/200w.mp4",
    "still_url": "https://media2.giphy.com/media/abc123/giphy_s.gif",
    "width": 480,
    "height": 270,
}


def gif_with(**changes):
    gif = dict(GIF)
    gif.update(changes)
    return gif


class ValidateGifTests(SimpleTestCase):

    def assertInvalid(self, raw):
        gif, error = _validate_gif(raw)
        self.assertIsNone(gif)
        self.assertEqual(error, "Invalid GIF.")

    def test_accepts_json_string_and_dict(self):
        self.assertEqual(_validate_gif(json.dumps(GIF)), (GIF, None))
        self.assertEqual(_validate_gif(GIF), (GIF, None))

    def test_accepts_other_giphy_media_hosts(self):
        raw = gif_with(still_url="https://i.giphy.com/abc123.gif")
        gif, error = _validate_gif(raw)
        self.assertIsNone(error)
        self.assertEqual(gif["still_url"], "https://i.giphy.com/abc123.gif")

    def test_drops_unknown_keys_and_truncates_title(self):
        gif, error = _validate_gif(gif_with(onload="alert(1)", title="x" * 300))
        self.assertIsNone(error)
        self.assertNotIn("onload", gif)
        self.assertEqual(len(gif["title"]), 200)

    def test_missing_title_becomes_empty_string(self):
        raw = dict(GIF)
        del raw["title"]
        gif, error = _validate_gif(raw)
        self.assertIsNone(error)
        self.assertEqual(gif["title"], "")

    def test_forces_provider(self):
        gif, _ = _validate_gif(gif_with(provider="evil"))
        self.assertEqual(gif["provider"], "giphy")

    def test_rejects_foreign_host(self):
        self.assertInvalid(gif_with(video_url="https://evil.example/x.mp4"))

    def test_rejects_lookalike_host(self):
        self.assertInvalid(
            gif_with(video_url="https://media.giphy.com.evil.example/x.mp4")
        )

    def test_rejects_http(self):
        self.assertInvalid(gif_with(video_url="http://media.giphy.com/x.mp4"))

    def test_rejects_javascript_url(self):
        self.assertInvalid(gif_with(still_url="javascript:alert(1)"))

    def test_rejects_missing_keys(self):
        raw = dict(GIF)
        del raw["still_url"]
        self.assertInvalid(raw)

    def test_rejects_bad_dimensions(self):
        for bad in (0, 5000, "wide", 1.5, True, None):
            with self.subTest(width=bad):
                self.assertInvalid(gif_with(width=bad))

    def test_rejects_non_string_id(self):
        self.assertInvalid(gif_with(id=["abc"]))

    def test_rejects_malformed_json(self):
        self.assertInvalid("{not json")

    def test_rejects_json_that_is_not_an_object(self):
        self.assertInvalid("[1, 2]")


class PostGifEndpointTests(TestCase):

    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/post_fixture.json", verbosity=0)
        self.client = APIClient()
        self.author = User.objects.get(pk=1)
        self.other = User.objects.get(pk=2)
        for user in (self.author, self.other):
            user.password = make_password("987password")
            user.save()

        # Post 1 belongs to user 1 in the fixture.
        self.post = Post.objects.get(pk=1)
        self.post.gif = GIF
        self.post.save()

    def login(self, user):
        self.client.login(username=user.email, password="987password")

    def test_create_post_with_gif_saves_and_returns_it(self):
        self.login(self.author)

        response = self.client.post(
            "/post/", {"content": "hello", "gif": json.dumps(GIF)}
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["post"]["gif"], GIF)
        self.assertEqual(Post.objects.latest("id").gif, GIF)

    def test_create_post_without_gif_returns_null(self):
        self.login(self.author)

        response = self.client.post("/post/", {"content": "hello"})

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json()["post"]["gif"])
        self.assertIsNone(Post.objects.latest("id").gif)

    def test_create_post_rejects_foreign_gif_host(self):
        self.login(self.author)
        count = Post.objects.count()
        bad = gif_with(video_url="https://evil.example/x.mp4")

        response = self.client.post(
            "/post/", {"content": "hello", "gif": json.dumps(bad)}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid GIF."})
        self.assertEqual(Post.objects.count(), count)

    def test_create_post_rejects_malformed_gif_json(self):
        self.login(self.author)
        count = Post.objects.count()

        response = self.client.post("/post/", {"content": "hello", "gif": "{not json"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Post.objects.count(), count)

    def test_update_post_remove_gif_by_author(self):
        self.login(self.author)

        response = self.client.patch(
            f"/post/{self.post.id}/", {"remove_gif": "true"}, format="multipart"
        )

        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertIsNone(self.post.gif)

    def test_update_post_remove_gif_by_staff(self):
        self.other.is_staff = True
        self.other.save()
        self.login(self.other)

        response = self.client.patch(
            f"/post/{self.post.id}/", {"remove_gif": "true"}, format="multipart"
        )

        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertIsNone(self.post.gif)

    def test_update_post_remove_gif_by_other_user_forbidden(self):
        self.login(self.other)

        response = self.client.patch(
            f"/post/{self.post.id}/", {"remove_gif": "true"}, format="multipart"
        )

        self.assertEqual(response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.gif, GIF)

    def test_update_post_without_remove_gif_keeps_gif(self):
        self.login(self.author)

        response = self.client.patch(
            f"/post/{self.post.id}/", {"content": "edited"}, format="multipart"
        )

        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, "edited")
        self.assertEqual(self.post.gif, GIF)

    def test_serializer_returns_null_gif(self):
        post = Post.objects.get(pk=2)  # fixture post, no GIF

        data = PostSerializer(post, context={"request": None}).data

        self.assertIsNone(data["gif"])
