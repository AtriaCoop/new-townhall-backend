from django.urls import path
from .views import ChatViewSet, MessageViewSet

urlpatterns = [
    path(
        "",
        ChatViewSet.as_view(
            {
                "post": "create_chat_request",
            }
        ),
        name="chats",
    ),
    path(
        "<int:id>/",
        ChatViewSet.as_view(
            {
                "get": "get_chat_request",
                "delete": "delete_chat_request",
            }
        ),
        name="chats_id",
    ),
    path(
        "messages/",
        MessageViewSet.as_view(
            {
                "post": "create_message_request",
            }
        ),
        name="messages",
    ),
]
