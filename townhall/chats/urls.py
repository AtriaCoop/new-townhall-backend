from django.urls import path
from .views import ChatViewSet, MessageViewSet

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
        ChatViewSet.as_view({"get": "get_chat_messages"}),
        name="chat_messages",
    ),
    path(
        "chats/send/",
        ChatViewSet.as_view({"post": "create_direct_message"}),
        name="create_direct_message",
    ),
    path(
        "groups/<str:group_name>/messages/",
        ChatViewSet.as_view({"get": "get_group_messages"}),
        name="group_messages",
    ),
    path(
        "groups/messages/",
        ChatViewSet.as_view({"post": "create_group_message"}),
        name="create_group_message",
    ),
    path(
        "chats/messages/",
        MessageViewSet.as_view(
            {
                "post": "create_message_request",
            }
        ),
        name="messages",
    ),
]
