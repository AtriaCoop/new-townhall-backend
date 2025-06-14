from django.urls import re_path
from chats.consumers import ChatConsumer, UserConsumer, GroupConsumer

websocket_urlpatterns = [
    re_path(r'ws/chats/(?P<chat_id>\w+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/groups/(?P<group_name>[^/]+)/$', GroupConsumer.as_asgi()),
    re_path(r'ws/users/(?P<user_id>\w+)/$', UserConsumer.as_asgi()),
]
