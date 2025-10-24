from django.urls import path

from posts.views import PostViewSet, CommentViewSet


urlpatterns = [
    path(
        "post/",
        PostViewSet.as_view(
            {
                "get": "get_post_all",
                "post": "create_post",
            }
        ),
        name="post",
    ),
    path(
        "post/<int:pk>/",
        PostViewSet.as_view(
            {"get": "get_post", "patch": "update_post", "delete": "delete_post"}
        ),
        name="post_id",
    ),
    path(
        "post/<int:pk>/like/",
        PostViewSet.as_view({"patch": "like_post"}),
    ),
    path(
        "comment/",
        CommentViewSet.as_view(
            {
                "post": "create_comment",
            }
        ),
        name="comment",
    ),
    path(
        "comment/<int:pk>/",
        CommentViewSet.as_view({"delete": "destroy", "patch": "update_comment"}),
    ),
    path("post/<int:pk>/report", PostViewSet.as_view({"post": "report_post"})),
]
