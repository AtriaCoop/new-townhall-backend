from django.urls import path
from .views import EventViewSet

urlpatterns = [
    path(
        "event/",
        EventViewSet.as_view({"get": "get_all_events", "post": "create_event"}),
        name="event",
    ),
    path(
        "event/<int:pk>/",
        EventViewSet.as_view(
            {
                "get": "get_event",
                "delete": "delete_event",
                "patch": "update_event",
            }
        ),
        name="event_detail",
    ),
    path(
        "event/<int:pk>/participate/",
        EventViewSet.as_view({"post": "participate"}),
        name="event_participate",
    ),
    path(
        "event/<int:pk>/unenroll/",
        EventViewSet.as_view({"post": "unenroll"}),
        name="event_unenroll",
    ),
]
