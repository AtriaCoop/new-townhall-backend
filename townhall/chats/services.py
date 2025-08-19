from django.core.exceptions import ValidationError
from typing import Optional
from .models import Chat, Message
from .daos import ChatDao, MessageDao
from .types import CreateChatData, CreateMessageData, UpdateMessageData
from django.db.models import Count
from django.db.models import QuerySet
import typing


class ChatServices:
    def get_chat(id: int) -> Optional[Chat]:
        try:
            chat = ChatDao.get_chat(id=id)
            return chat
        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with the given id: {id}, does not exist.")

    def get_chat_all() -> QuerySet[Chat]:
        chats = ChatDao.get_chat_all()
        if not chats.exists():
            raise ValidationError("No chats were found.")
        return chats

    def delete_chat(id: int) -> None:
        try:
            ChatDao.delete_chat(id=id)
        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with the given id: {id}, does not exist.")

    @staticmethod
    def get_or_create_chat(data: CreateChatData):
        try:
            participant_ids = sorted(data.participant_ids)

            # Check all chats that this user is in
            possible_chats = (
                Chat.objects.annotate(num_participants=Count("participants"))
                .filter(
                    participants__id__in=participant_ids,
                    num_participants=len(participant_ids),
                )
                .distinct()
            )

            for chat in possible_chats:
                existing_ids = sorted(chat.participants.values_list("id", flat=True))
                if existing_ids == participant_ids:
                    return chat, False  # Found existing chat

            # Create new chat if none found
            chat = ChatDao.create_chat(create_chat_data=data)
            return chat, True

        except ValidationError:
            raise

    def add_user(chat_id: int, user_id: int):
        try:
            ChatDao.add_user(chat_id=chat_id, user_id=user_id)
        except ValidationError as e:
            raise ValidationError(f"Failed to add user: {e}")

    @staticmethod
    def update_chat_participants(chat_id: int, new_participant_ids: list[int]) -> Chat:
        try:
            ChatDao.get_chat(chat_id)
            if len(new_participant_ids) < 2:
                raise ValidationError("Chat must have at least two participants.")

            updated_chat = ChatDao.update_chat_participants(
                chat_id=chat_id, new_participant_ids=new_participant_ids
            )
            return updated_chat

        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with id {chat_id} does not exist.")

        except Exception as e:
            raise ValidationError(f"Failed: {str(e)}")


class MessageServices:
    def create_message(create_message_data: CreateMessageData) -> Optional[Message]:
        try:
            message = MessageDao.create_message(create_message_data=create_message_data)

            return message
        except ValidationError:
            raise

    def get_message(id: int) -> typing.Optional[Message]:
        try:
            message = MessageDao.get_message(id=id)
            return message
        except Message.DoesNotExist:
            raise ValidationError(f"Message with the given id: {id}, does not exist.")

    def delete_message(id: int) -> None:
        try:
            MessageDao.delete_message(id=id)
        except Message.DoesNotExist:
            raise ValidationError(f"Message with the given id: {id}, does not exist.")

    def update_message(id: int, update_message_data: UpdateMessageData) -> None:
        try:
            MessageDao.update_message(id=id, update_message_data=update_message_data)
        except Message.DoesNotExist:
            raise ValidationError(f"Message with the given id: {id}, does not exist.")
