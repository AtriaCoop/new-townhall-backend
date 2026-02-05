from typing import Optional
from .models import Chat, Message
from .types import CreateChatData, CreateMessageData, UpdateMessageData
from django.db.models import QuerySet
from django.db import DatabaseError
from django.core.exceptions import ValidationError
from users.services import UserServices


class ChatDao:
    @staticmethod
    def get_chat(id: int) -> Optional[Chat]:
        return Chat.objects.prefetch_related("participants").get(id=id)

    @staticmethod
    def get_chat_all() -> QuerySet[Chat]:
        try:
            return Chat.objects.prefetch_related("participants").all()
        except DatabaseError as error:
            print(f"A Database Error has occured {error}")
            return None

    @staticmethod
    def delete_chat(id: int) -> None:
        Chat.objects.get(id=id).delete()

    @staticmethod
    def create_chat(create_chat_data: CreateChatData) -> Optional[Chat]:
        chat = Chat.objects.create(
            name=create_chat_data.name,
        )

        chat.participants.add(*create_chat_data.participant_ids)
        return chat

    @staticmethod
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
    @staticmethod
    def create_message(create_message_data: CreateMessageData) -> Message:
        message = Message.objects.create(
            user_id=create_message_data.user_id,
            chat_id=create_message_data.chat_id,
            content=create_message_data.content,
            image_content=create_message_data.image_content,
            sent_at=create_message_data.sent_at,
        )

        return message

    @staticmethod
    def get_message(id: int) -> Optional[Message]:
        return Message.objects.get(id=id)

    @staticmethod
    def delete_message(id: int) -> None:
        Message.objects.get(id=id).delete()

    @staticmethod
    def update_message(id: int, update_message_data: UpdateMessageData) -> None:
        message = Message.objects.get(id=id)

        if update_message_data.user_id:
            message.user_id = update_message_data.user_id
        if update_message_data.chat_id:
            message.chat_id = update_message_data.chat_id
        if update_message_data.content:
            message.content = update_message_data.content
        if update_message_data.image_content:
            message.image_content = update_message_data.image_content
        if update_message_data.sent_at:
            message.sent_at = update_message_data.sent_at

        message.save()
