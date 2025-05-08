"""
URL configuration for townhall project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from debug_toolbar.toolbar import debug_toolbar_urls

from users.views import UserViewSet, login_user



urlpatterns = [
    # path("users/", include("users.urls")),
    # path("posts/", include("posts.urls")),
    # path("chats/", include("chats.urls")),
    path ("admin/", admin.site.urls),
    path("auth/login/", login_user, name="login_user"),
    path (
        "user/",
        UserViewSet.as_view (
            {
                "get": "get_user_all",
                "post": "create_user",
            }
        ),
        name="user"
    ),
    path (
        "user/<int:user_id>/",
        UserViewSet.as_view (
            {
                "get": "get_user",
                "delete": "delete_user",
                "patch": "update_user",
            }
        ),
        name="user_id"
    ),
    path (
        "user/<int:pk>/complete_profile/",
        UserViewSet.as_view (
            {
                "post": "complete_profile",
            }
        ),
        name="complete_profile"
    )
] + debug_toolbar_urls()

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
