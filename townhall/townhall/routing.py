from django.urls import re_path
from chats.consumers import ChatConsumer, UserConsumer

websocket_urlpatterns = [
    re_path(r'ws/chats/(?P<chat_id>\w+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/users/(?P<user_id>\w+)/$', UserConsumer.as_asgi()),
]