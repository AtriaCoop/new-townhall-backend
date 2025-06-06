from django.core.exceptions import ValidationError
from typing import Optional
from .models import Chat, Message
from .daos import ChatDao, MessageDao
from .types import CreateChatData, CreateMessageData
from django.db.models import Count


class ChatServices:
    def get_chat(id: int) -> Optional[Chat]:
        try:
            chat = ChatDao.get_chat(id=id)
            return chat
        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with the given id: {id}, does not exist.")

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


class MessageServices:
    def create_message(create_message_data: CreateMessageData) -> Optional[Message]:
        try:
            message = MessageDao.create_message(create_message_data=create_message_data)

            return message
        except ValidationError:
            raise
