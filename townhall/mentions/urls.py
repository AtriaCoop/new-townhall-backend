from django.urls import path

from mentions.views import MentionViewSet

urlpatterns = [
    path(
        "mention_users/",
        MentionViewSet.as_view({"post": "mention_users"}),
        name="mention_users",
    ),
]
