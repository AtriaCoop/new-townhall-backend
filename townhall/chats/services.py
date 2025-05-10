from django.core.exceptions import ValidationError
from typing import Optional
from .models import Chat, Message
from .daos import ChatDao, MessageDao
from .types import CreateChatData, CreateMessageData


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

    def create_chat(create_chat_data: CreateChatData) -> Optional[Chat]:
        try:
            chat = ChatDao.create_chat(create_chat_data=create_chat_data)

            return chat
        except ValidationError:
            raise


class MessageServices:
    def create_message(create_message_data: CreateMessageData) -> Optional[Message]:
        try:
            message = MessageDao.create_message(create_message_data=create_message_data)

            return message
        except ValidationError:
            raise
