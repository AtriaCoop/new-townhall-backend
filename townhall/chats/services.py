from django.core.exceptions import ValidationError
from typing import Optional
from .models import Chat
from .daos import ChatDao
from .types import CreateChatData


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
