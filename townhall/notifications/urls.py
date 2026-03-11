from django.urls import path
from .views import NotificationViewSet

urlpatterns = [
    path(
        "notifications/",
        NotificationViewSet.as_view({"get": "get_notifications"}),
        name="notifications",
    ),
    path(
        "notifications/unread-count/",
        NotificationViewSet.as_view({"get": "unread_count"}),
        name="notifications_unread_count",
    ),
    path(
        "notifications/mark-all-read/",
        NotificationViewSet.as_view({"post": "mark_all_read"}),
        name="notifications_mark_all_read",
    ),
    path(
        "notifications/<int:pk>/mark-read/",
        NotificationViewSet.as_view({"post": "mark_read"}),
        name="notification_mark_read",
    ),
]
