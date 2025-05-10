from typing import Optional
from .models import Chat, Message
from .types import CreateChatData, CreateMessageData


class ChatDao:
    def get_chat(id: int) -> Optional[Chat]:
        return Chat.objects.prefetch_related("participants").get(id=id)

    def delete_chat(id: int) -> None:
        Chat.objects.get(id=id).delete()

    def create_chat(create_chat_data: CreateChatData) -> Optional[Chat]:
        chat = Chat.objects.create(
            name=create_chat_data.name,
        )

        chat.participants.add(*create_chat_data.participant_ids)
        return chat

class MessageDao:
    def create_message(create_message_data: CreateMessageData) -> Optional[Message]:
        message = Message.objects.create(
            user_id = create_message_data.user_id,
            chat_id = create_message_data.chat_id,
            content = create_message_data.content,
            image_content = create_message_data.image_content,
            sent_at = create_message_data.sent_at
        )

        return message