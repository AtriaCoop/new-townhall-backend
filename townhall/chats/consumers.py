import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # Join chat group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave chat group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        from chats.models import Chat
        from chats.services import MessageServices
        from chats.types import CreateMessageData
        from datetime import datetime

        data = json.loads(text_data)
        message = data['message']
        sender = data['sender']

        # ✅ Save the message
        await sync_to_async(MessageServices.create_message)(
            CreateMessageData(
                user_id=sender,
                chat_id=int(self.chat_id),
                content=message,
                sent_at=datetime.now()
            )
        )

        # Broadcast to chat group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
            }
        )

        # Broadcast to user listeners
        chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)
        participant_ids = await sync_to_async(list)(chat.participants.values_list("id", flat=True))

        for user_id in participant_ids:
            await self.channel_layer.group_send(
                f'user_{user_id}',
                {
                    'type': 'user_message',
                    'chat_id': self.chat_id,
                    'message': message,
                    'sender': sender,
                }
            )

    # Receive message from group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))


class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'user_{self.user_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def user_message(self, event):
        await self.send(text_data=json.dumps(event))
