from typing import Optional
from .models import Chat
from .types import CreateChatData


class ChatDao:
    def get_chat(id: int) -> Optional[Chat]:
        return Chat.objects.get(id=id)

    def delete_chat(id: int) -> None:
        Chat.objects.get(id=id).delete()

    def create_chat(create_chat_data: CreateChatData) -> Optional[Chat]:
        chat = Chat.objects.create(
            name=create_chat_data.name,
            created_at=create_chat_data.created_at,
        )

        chat.participants.add(*create_chat_data.participant_ids)
        return chat
