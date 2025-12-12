from django.urls import path
from .views import ActivityViewSet

urlpatterns = [
    path(
        "activities/",
        ActivityViewSet.as_view(
            {
                "get": "get_user_activities",
            }
        ),
        name="activities",
    ),
]
