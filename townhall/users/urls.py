from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from debug_toolbar.toolbar import debug_toolbar_urls

from users.views import UserViewSet, login_user, logout_user, get_csrf_token


urlpatterns = [
    path("auth/login/", login_user, name="login_user"),
    path("auth/logout/", logout_user),
    path("auth/csrf/", get_csrf_token),
    path(
        "user/",
        UserViewSet.as_view(
            {
                "get": "get_user_all",
                "post": "create_user",
            }
        ),
        name="user",
    ),
    path(
        "user/<int:user_id>/",
        UserViewSet.as_view(
            {
                "get": "get_user",
                "delete": "delete_user",
                "patch": "update_user",
            }
        ),
        name="user_id",
    ),
    path(
        "user/<int:pk>/complete_profile/",
        UserViewSet.as_view(
            {
                "post": "complete_profile",
            }
        ),
        name="complete_profile",
    ),
    path(
        "user/mention/",
        UserViewSet.as_view({"get": "mention_user"}),
        name="mention_user",
    ),
] + debug_toolbar_urls()

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
