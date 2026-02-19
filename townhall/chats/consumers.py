import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("🟥 ChatConsumer connected")
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"chat_{self.chat_id}"

        # Join chat group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave chat group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket (broadcast only — message is already saved via REST API)
    async def receive(self, text_data):
        from chats.models import Chat
        from users.models import User

        data = json.loads(text_data)
        message = data["message"]
        sender = data["sender"]

        user = await sync_to_async(User.objects.get)(id=sender)

        # Broadcast to chat group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender_id": sender,
                "full_name": user.full_name,
                "organization": user.primary_organization,
                "profile_image": (
                    user.profile_image.url if user.profile_image else None
                ),
                "timestamp": str(timezone.now()),
            },
        )

        # Broadcast to user listeners
        chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)
        participant_ids = await sync_to_async(list)(
            chat.participants.values_list("id", flat=True),
        )

        for user_id in participant_ids:
            await self.channel_layer.group_send(
                f"user_{user_id}",
                {
                    "type": "user_message",
                    "chat_id": self.chat_id,
                    "message": message,
                    "sender": sender,
                },
            )

    # Receive message from group
    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                    "full_name": event["full_name"],
                    "organization": event["organization"],
                    "profile_image": event["profile_image"],
                    "timestamp": event.get("timestamp", ""),
                }
            )
        )


class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_info = self.scope["url_route"]["kwargs"]["user_id"]
        print("🟦 UserConsumer connected for user:", user_info)
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"user_{self.user_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def user_message(self, event):
        await self.send(text_data=json.dumps(event))


class GroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        group_info = self.scope["url_route"]["kwargs"]["group_name"]
        print("🟩 GroupConsumer connected for group:", group_info)
        self.group_name = self.scope["url_route"]["kwargs"]["group_name"]
        self.room_group_name = f"group_{self.group_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket (broadcast only — message is already saved via REST API)
    async def receive(self, text_data):
        from users.models import User

        data = json.loads(text_data)
        message = data["message"]
        sender = data["sender"]

        user = await sync_to_async(User.objects.get)(id=sender)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "group_message",
                "message": message,
                "sender_id": sender,
                "full_name": user.full_name,
                "organization": user.primary_organization,
                "profile_image": (
                    user.profile_image.url if user.profile_image else None
                ),
                "timestamp": str(timezone.now()),
            },
        )

    async def group_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                    "full_name": event["full_name"],
                    "organization": event["organization"],
                    "profile_image": event["profile_image"],
                    "timestamp": event.get("timestamp", ""),
                }
            )
        )
