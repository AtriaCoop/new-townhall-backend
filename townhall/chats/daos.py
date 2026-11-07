import typing
from datetime import datetime
from typing import Optional

from users.models import User

from .models import Chat, ChatReadStatus, GroupMessage, Message, MessageReaction
from .types import (
    CreateChatData,
    CreateMessageData,
    UpdateMessageData,
    ToggleMessageReactionData,
)
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
    def get_user_chats(user_id: int) -> QuerySet[Chat]:
        return (
            Chat.objects.prefetch_related("participants")
            .filter(participants__id=user_id)
            .exclude(hidden_by__id=user_id)
            .distinct()
        )

    @staticmethod
    def soft_delete_chat_request(id: int, user_id: int) -> None:
        chat = Chat.objects.get(id=id)
        user = User.objects.get(id=user_id)

        chat.hidden_by.add(user)

    @staticmethod
    def delete_chat(id: int) -> None:
        Chat.objects.get(id=id).delete()

    @staticmethod
    def create_chat(create_chat_data: CreateChatData) -> Optional[Chat]:
        chat = Chat.objects.create(
            name=create_chat_data.name,
            is_group=create_chat_data.is_group,
        )

        chat.participants.add(*create_chat_data.participant_ids)
        return chat

    @staticmethod
    def unhide_chat_and_get_participant_ids(chat_id: int) -> list[int]:
        chat = Chat.objects.get(id=chat_id)
        chat.hidden_by.clear()
        return list(chat.participants.values_list("id", flat=True))

    @staticmethod
    def get_unread_message_summaries(
        user_id: int,
    ) -> list[tuple[int, int, Message]]:
        summaries = []
        chats = Chat.objects.filter(participants__id=user_id).exclude(
            hidden_by__id=user_id
        )

        for chat in chats:
            read_status = ChatReadStatus.objects.filter(
                user_id=user_id, chat_id=chat.id
            ).first()
            messages = Message.objects.filter(chat_id=chat.id).exclude(user_id=user_id)
            if read_status:
                messages = messages.filter(sent_at__gt=read_status.last_read_at)

            count = messages.count()
            if count == 0:
                continue

            latest_message = (
                messages.select_related("user").order_by("-sent_at").first()
            )

            summaries.append((chat.id, count, latest_message))

        return summaries

    @staticmethod
    def update_chat_read_status(
        chat_id: int, user_id: int, last_read_at: datetime
    ) -> None:
        ChatReadStatus.objects.update_or_create(
            user_id=user_id,
            chat_id=chat_id,
            defaults={"last_read_at": last_read_at},
        )

    @staticmethod
    def mark_delivered_messages_as_read(chat_id: int, user_id: int) -> list[int]:
        messages = Message.objects.filter(
            chat_id=chat_id,
            status=Message.Status.DELIVERED,
        ).exclude(user_id=user_id)
        message_ids = list(messages.values_list("id", flat=True))
        messages.update(status=Message.Status.READ)
        return message_ids

    @staticmethod
    def get_group_messages(group_name: str) -> QuerySet[GroupMessage]:
        return (
            GroupMessage.objects.filter(group_name=group_name)
            .select_related("user")
            .order_by("sent_at")
        )

    @staticmethod
    def create_group_message(
        user: User, group_name: str, content: str, image=None
    ) -> GroupMessage:
        return GroupMessage.objects.create(
            user=user,
            group_name=group_name,
            content=content,
            image=image,
        )

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
    def get_chat_messages_order_by_sent_at(chat_id: int) -> QuerySet[Message]:
        return Message.objects.filter(chat_id=chat_id).order_by("sent_at")

    @staticmethod
    def update_chat_participants(chat_id: int, new_participant_ids: list[int]) -> Chat:
        chat = Chat.objects.get(id=chat_id)
        chat.participants.set(new_participant_ids)
        return chat

    @staticmethod
    def remove_user(chat_id: int, user_id: int) -> None:
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with id {chat_id} does not exist.")

        if not chat.participants.filter(id=user_id).exists():
            raise ValidationError(
                f"User {user_id} is not a participant in chat {chat_id}."
            )

        user = UserServices.get_user(user_id)
        chat.participants.remove(user)


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
        if update_message_data.is_edited:
            message.is_edited = update_message_data.is_edited
        if update_message_data.status is not None:
            message.status = update_message_data.status

        message.save()


class ReactionDao:
    @staticmethod
    def _get_reaction(**filters) -> typing.Optional[MessageReaction]:
        try:
            return MessageReaction.objects.get(**filters)
        except MessageReaction.DoesNotExist:
            return None

    @staticmethod
    def _create_reaction(**fields) -> MessageReaction:
        return MessageReaction.objects.create(**fields)

    @staticmethod
    def get_reaction(
        message_id: int, user_id: int, reaction_type: str
    ) -> typing.Optional[MessageReaction]:
        return ReactionDao._get_reaction(
            message_id=message_id,
            user_id=user_id,
            reaction_type=reaction_type,
        )

    @staticmethod
    def create_reaction(reaction_data: ToggleMessageReactionData) -> MessageReaction:
        return ReactionDao._create_reaction(
            message_id=reaction_data.message_id,
            user_id=reaction_data.user_id,
            reaction_type=reaction_data.reaction_type,
        )

    @staticmethod
    def delete_reaction(reaction: MessageReaction) -> None:
        reaction.delete()
