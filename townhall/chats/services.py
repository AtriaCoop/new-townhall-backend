import typing

from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from django.db.models import QuerySet
from django.utils import timezone
from typing import Optional

from rest_framework.exceptions import APIException

from posts.services import ReactionServices as PostReactionServices
from .serializers import ChatSerializer, MessageSerializer
from users.models import User

from .daos import ChatDao, MessageDao, ReactionDao
from .models import Chat, GroupMessage, Message
from .types import (
    CreateChatData,
    CreateMessageData,
    ToggleMessageReactionData,
    UpdateMessageData,
)


class ChatServices:
    @staticmethod
    def create_group_message(
        user: User,
        group_name: str,
        content: str,
        image=None,
    ) -> GroupMessage:
        try:
            return ChatDao.create_group_message(
                user=user,
                group_name=group_name,
                content=content,
                image=image,
            )
        except DatabaseError as error:
            raise APIException(
                "A database error occurred while creating a group message."
            ) from error

    @staticmethod
    def delete_group_message(message_id: int) -> None:
        try:
            ChatDao.delete_group_message(message_id=message_id)
        except GroupMessage.DoesNotExist as error:
            raise ValidationError("Message not found") from error
        except DatabaseError as error:
            raise APIException(
                "A database error occurred while deleting a group message."
            ) from error

    @staticmethod
    def get_group_messages(group_name: str) -> list[GroupMessage]:
        try:
            return list(ChatDao.get_group_messages(group_name=group_name))
        except DatabaseError as error:
            raise APIException(
                "A database error occurred while fetching group messages."
            ) from error

    @staticmethod
    def mark_chat_read(chat_id: int, user_id: int) -> list[int]:
        try:
            with transaction.atomic():
                ChatDao.get_chat(id=chat_id)
                ChatDao.update_chat_read_status(
                    chat_id=chat_id,
                    user_id=user_id,
                    last_read_at=timezone.now(),
                )
                return ChatDao.mark_delivered_messages_as_read(
                    chat_id=chat_id,
                    user_id=user_id,
                )
        except Chat.DoesNotExist as error:
            raise ValidationError("Chat not found") from error
        except DatabaseError as error:
            raise APIException(
                "A database error occurred while marking the chat as read."
            ) from error

    @staticmethod
    def get_unread_counts(user_id: int) -> dict[int, dict]:
        try:
            summaries = ChatDao.get_unread_message_summaries(user_id=user_id)
        except DatabaseError as error:
            raise APIException(
                "A database error occurred while fetching unread counts."
            ) from error

        result = {}
        for chat_id, count, latest_message in summaries:
            sender = latest_message.user
            result[chat_id] = {
                "count": count,
                "sender_id": sender.id,
                "sender_name": sender.full_name,
                "sender_image": (
                    sender.profile_image.url if sender.profile_image else None
                ),
                "last_message": latest_message.content,
                "timestamp": latest_message.sent_at.isoformat(),
            }

        return result

    @staticmethod
    def get_chat(id: int) -> Optional[Chat]:
        try:
            chat = ChatDao.get_chat(id=id)
            return chat
        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with the given id: {id}, does not exist.")

    @staticmethod
    def get_chat_all() -> QuerySet[Chat]:
        chats = ChatDao.get_chat_all()
        if chats is None or not chats.exists():
            raise ValidationError("No chats were found.")
        return chats

    @staticmethod
    def get_user_chats(user_id: int):
        try:
            chats = ChatDao.get_user_chats(user_id=user_id)
            serializer = ChatSerializer(chats, many=True)
            return serializer.data
        except DatabaseError as e:
            raise APIException(
                "A database error occurred while fetching user chats."
            ) from e

    @staticmethod
    def soft_delete_chat_request(id: int, user_id: int) -> None:
        try:
            ChatDao.soft_delete_chat_request(id=id, user_id=user_id)
        except DatabaseError as e:
            raise APIException(
                "A database error occurred while soft deleting the chat request."
            ) from e

    @staticmethod
    def delete_chat(id: int) -> None:
        try:
            ChatDao.delete_chat(id=id)
        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with the given id: {id}, does not exist.")

    @staticmethod
    def get_or_create_chat(data: CreateChatData):
        try:
            participant_ids = sorted(data.participant_ids)

            # Find chats containing ALL specified participants
            possible_chats = Chat.objects.all()
            for pid in participant_ids:
                possible_chats = possible_chats.filter(participants__id=pid)

            # Verify exact participant match (no extra participants)
            for chat in possible_chats:
                existing_ids = sorted(chat.participants.values_list("id", flat=True))
                if existing_ids == participant_ids and chat.is_group == data.is_group:
                    return chat, False  # Found existing chat

            # Check if any participant has disabled DMs before creating
            participants = User.objects.filter(id__in=participant_ids)
            for participant in participants:
                if not participant.allow_dms:
                    raise ValidationError("This user does not accept direct messages.")

            # Create new chat if none found
            chat = ChatDao.create_chat(create_chat_data=data)
            return chat, True

        except ValidationError:
            raise

    @staticmethod
    def get_chat_messages(chat_id: int) -> QuerySet[Message]:
        try:
            messages = MessageDao.get_chat_messages(chat_id=chat_id)
            return messages
        except Chat.DoesNotExist:
            raise ValidationError(f"Chat with the given id: {chat_id}, does not exist.")

    @staticmethod
    def get_chat_messages_order_by_sent_at(chat_id: int) -> QuerySet[Message]:
        try:
            messages = ChatDao.get_chat_messages_order_by_sent_at(chat_id=chat_id)
            serializer = MessageSerializer(messages, many=True)
            return serializer.data
        except DatabaseError as e:
            raise APIException(
                "A database error occurred while fetching chat messages "
                "ordered by sent_at."
            ) from e

    @staticmethod
    def add_user(chat_id: int, user_id: int):
        try:
            ChatDao.add_user(chat_id=chat_id, user_id=user_id)
            return f"User {user_id} successfully added to chat {chat_id}."
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

    @staticmethod
    def remove_user(chat_id: int, user_id: int) -> str:
        try:
            ChatDao.remove_user(chat_id=chat_id, user_id=user_id)
            return f"User {user_id} successfully removed from chat {chat_id}."
        except ValidationError as e:
            raise ValidationError(f"Failed to remove user: {e}")


class MessageServices:
    @staticmethod
    def create_direct_message(
        user_id: int,
        chat_id: int,
        content: str,
        image_content: Optional[str] = None,
    ) -> tuple[Message, list[int]]:
        try:
            with transaction.atomic():
                ChatDao.get_chat(id=chat_id)
                message = MessageDao.create_message(
                    create_message_data=CreateMessageData(
                        user_id=user_id,
                        chat_id=chat_id,
                        content=content,
                        image_content=image_content,
                    )
                )
                participant_ids = ChatDao.unhide_chat_and_get_participant_ids(
                    chat_id=chat_id
                )
            return message, participant_ids
        except Chat.DoesNotExist as error:
            raise ValidationError(
                f"Chat with the given id: {chat_id}, does not exist."
            ) from error
        except DatabaseError as error:
            raise APIException(
                "A database error occurred while sending the message."
            ) from error

    @staticmethod
    def create_message(create_message_data: CreateMessageData) -> Optional[Message]:
        try:
            message = MessageDao.create_message(create_message_data=create_message_data)

            return message
        except ValidationError:
            raise

    @staticmethod
    def get_message(id: int) -> typing.Optional[Message]:
        try:
            message = MessageDao.get_message(id=id)
            return message
        except Message.DoesNotExist:
            raise ValidationError(f"Message with the given id: {id}, does not exist.")

    @staticmethod
    def delete_message(id: int) -> None:
        try:
            MessageDao.delete_message(id=id)
        except Message.DoesNotExist:
            raise ValidationError(f"Message with the given id: {id}, does not exist.")

    @staticmethod
    def update_message(id: int, update_message_data: UpdateMessageData) -> bool:
        try:
            original_message = MessageDao.get_message(id=id)

            # If the content changed, mark the message as edited
            if original_message.content != update_message_data.content:
                update_message_data.is_edited = True
            else:
                update_message_data.is_edited = original_message.is_edited

            MessageDao.update_message(id=id, update_message_data=update_message_data)
            is_edited = MessageDao.get_message(id=id).is_edited

            return is_edited

        except Message.DoesNotExist:
            raise ValidationError(f"Message with the given id: {id}, does not exist.")


class ReactionServices:
    @staticmethod
    def toggle_reaction_on_message(
        reaction_data: ToggleMessageReactionData,
    ) -> typing.Tuple[bool, str]:
        MessageServices.get_message(id=reaction_data.message_id)
        PostReactionServices._validate_user_exists(reaction_data.user_id)
        PostReactionServices._validate_reaction_type(reaction_data.reaction_type)
        return PostReactionServices._toggle_reaction(
            reaction_data.reaction_type,
            lambda: ReactionDao.get_reaction(
                message_id=reaction_data.message_id,
                user_id=reaction_data.user_id,
                reaction_type=reaction_data.reaction_type,
            ),
            lambda: ReactionDao.create_reaction(reaction_data),
            ReactionDao.delete_reaction,
        )
