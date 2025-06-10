from django.urls import path
from .views import ChatViewSet

urlpatterns = [
    path(
        "chats/",
        ChatViewSet.as_view(
            {
                "get": "get_user_chats",
                "post": "create_chat_request",
            }
        ),
        name="chats",
    ),
    path(
        "chats/<int:id>/",
        ChatViewSet.as_view(
            {
                "get": "get_chat_request",
                "delete": "delete_chat_request",
            }
        ),
        name="chats_id",
    ),
    path(
        "chats/<int:id>/messages/",
        ChatViewSet.as_view(
            {
                "get": "get_chat_messages"
            }
        ),
        name="chat_messages",
    ),
    path(
        "groups/<str:group_name>/messages/",
        ChatViewSet.as_view(
            {
                "get": "get_group_messages"
            }
        ),
        name="group_messages",
    ),
]
