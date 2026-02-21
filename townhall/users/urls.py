from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from debug_toolbar.toolbar import debug_toolbar_urls

from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    TagViewSet,
    ReportViewSet,
    login_user,
    logout_user,
    get_csrf_token,
    check_session,
    change_password,
    forgot_password,
    reset_password,
)

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tag")

urlpatterns = [
    path("auth/login/", login_user, name="login_user"),
    path("auth/logout/", logout_user),
    path("auth/csrf/", get_csrf_token),
    path("auth/session/", check_session, name="check_session"),
    path("auth/change-password/", change_password, name="change_password"),
    path("auth/forgot-password/", forgot_password, name="forgot_password"),
    path("auth/reset-password/", reset_password, name="reset_password"),
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
    path(
        "user/report/",
        ReportViewSet.as_view({"post": "create_report_request"}),
        name="report",
    ),
    path(
        "user/report/<int:report_id>/",
        ReportViewSet.as_view({"get": "get_report"}),
        name="report_id",
    ),
    path("", include(router.urls)),  # <-- Make sure this is here
] + debug_toolbar_urls()

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
