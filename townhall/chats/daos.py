from typing import Optional
from .models import Chat, Message
from .types import CreateChatData, CreateMessageData
from django.db.models import QuerySet
from django.db import DatabaseError
from django.core.exceptions import ValidationError
from users.services import UserServices


class ChatDao:
    def get_chat(id: int) -> Optional[Chat]:
        return Chat.objects.prefetch_related("participants").get(id=id)

    @staticmethod
    def get_chat_all() -> QuerySet[Chat]:
        try:
            return Chat.objects.prefetch_related("participants").all()
        except DatabaseError as error:
            print(f"A Database Error has occured {error}")
            return None

    def delete_chat(id: int) -> None:
        Chat.objects.get(id=id).delete()

    def create_chat(create_chat_data: CreateChatData) -> Optional[Chat]:
        chat = Chat.objects.create(
            name=create_chat_data.name,
        )

        chat.participants.add(*create_chat_data.participant_ids)
        return chat

    def add_user(chat_id: int, user_id: int) -> None:

        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with id {chat_id} does not exist.")

        if chat.participants.filter(id=user_id).exists():
            raise ValidationError(
                f"User {user_id} is already a participant in chat {chat_id}."
            )

        user = UserServices.get_user(user_id)
        chat.participants.add(user)

    @staticmethod
    def update_chat_participants(chat_id: int, new_participant_ids: list[int]) -> Chat:
        chat = Chat.objects.get(id=chat_id)
        chat.participants.set(new_participant_ids)
        return chat


class MessageDao:
    def create_message(create_message_data: CreateMessageData) -> Message:
        message = Message.objects.create(
            user_id=create_message_data.user_id,
            chat_id=create_message_data.chat_id,
            content=create_message_data.content,
            image_content=create_message_data.image_content,
            sent_at=create_message_data.sent_at,
        )

        return message
