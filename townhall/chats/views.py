from django.core.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from users.models import User
from .serializers import (
    ChatSerializer,
    MessageSerializer,
    CreateChatSerializer,
    OptionalMessageSerializer,
    MessageStatusSerializer,
)
from posts.views import PostViewSet
from .services import ChatServices, MessageServices, ReactionServices
from .types import (
    CreateChatData,
    CreateMessageData,
    ToggleMessageReactionData,
    UpdateMessageData,
)
from django.utils import timezone
from .models import Chat, Message
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging


logger = logging.getLogger(__name__)


class ChatViewSet(viewsets.ModelViewSet):

    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    # GET One Chat
    @action(detail=True, methods=["get"], url_path="chats")
    @permission_classes([IsAuthenticated])
    def get_chat_request(self, request, id):
        chat_id = id

        try:
            chat = ChatServices.get_chat(chat_id)
            response_serializer = ChatSerializer(chat)

            return Response(
                {
                    "message": "Chat Retrieved Successfully",
                    "success": True,
                    "data": response_serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {
                    "message": str(e),
                    "success": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    # GET all chats for a user
    @action(detail=False, methods=["get"], url_path="chats")
    @permission_classes([IsAuthenticated])
    def get_user_chats(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response(
                {"message": "Missing user_id", "success": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = int(user_id)
        except ValueError:
            return Response(
                {"message": "user_id must be a valid integer", "success": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chats = ChatServices.get_user_chats(user_id=user_id)

        return Response(
            {
                "message": "Chats fetched successfully",
                "success": True,
                "data": chats,
            },
            status=status.HTTP_200_OK,
        )

    # DELETE (Hide) Chat — soft delete, preserves messages
    @action(detail=True, methods=["delete"], url_path="chats")
    @permission_classes([IsAuthenticated])
    def delete_chat_request(self, request, id):
        try:
            ChatServices.soft_delete_chat_request(id=id, user_id=request.user.id)

            return Response(
                {
                    "message": "Chat hidden successfully",
                    "success": True,
                },
                status=status.HTTP_200_OK,
            )
        except Chat.DoesNotExist:
            return Response(
                {
                    "message": "Chat not found",
                    "success": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except User.DoesNotExist:
            return Response(
                {
                    "message": "User not found",
                    "success": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    # POST (Create) Chat
    @action(detail=False, methods=["post"], url_path="chats")
    @permission_classes([IsAuthenticated])
    def create_chat_request(self, request):
        serializer = CreateChatSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "message": str(serializer.errors),
                    "success": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        create_chat_data = CreateChatData(
            name=validated_data["name"],
            participant_ids=validated_data["participants"],
            is_group=validated_data.get("is_group", False),
        )

        try:
            chat, created = ChatServices.get_or_create_chat(create_chat_data)
            if not created:
                # Unhide for all participants when a chat is reused
                chat.hidden_by.clear()
            response_serializer = ChatSerializer(chat)

            return Response(
                {
                    "message": (
                        "Chat Created Successfully"
                        if created
                        else "Chat Already Exists"
                    ),
                    "success": True,
                    "data": response_serializer.data,
                },
                status=(status.HTTP_201_CREATED if created else status.HTTP_200_OK),
            )
        except ValidationError as e:
            return Response(
                {
                    "message": str(e),
                    "success": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # PATCH (Update) Chat
    @action(detail=True, methods=["patch"], url_path="chats")
    @permission_classes([IsAuthenticated])
    def update_chat_participants(self, request, id):
        participant_ids = request.data.get("participant_ids", [])

        try:
            chat = ChatServices.update_chat_participants(
                chat_id=id, new_participant_ids=participant_ids
            )
            data = ChatSerializer(chat).data
            return Response(
                {
                    "message": "Chat participants updated successfully.",
                    "success": True,
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response(
                {"message": str(e), "success": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"message": f"Unexpected error: {str(e)}", "success": False},
                status=500,
            )

    # GET Message
    @action(detail=True, methods=["get"], url_path="messages")
    @permission_classes([IsAuthenticated])
    def get_chat_messages(self, request, id):
        try:
            data = MessageServices.get_chat_messages_order_by_sent_at(chat_id=id)
            return Response({"messages": data})
        except Message.DoesNotExist:
            return Response(
                {"message": "Chat not found", "success": False},
                status=status.HTTP_404_NOT_FOUND,
            )

    # POST Message
    @action(detail=False, methods=["post"], url_path="direct-message")
    @permission_classes([IsAuthenticated])
    def create_direct_message(self, request):
        try:
            user = request.user
            chat_id = request.data.get("chat_id")
            content = request.data.get("content", "")
            image = request.FILES.get("image_content", None)

            if not chat_id:
                return Response(
                    {"success": False, "error": "chat_id is required"},
                    status=400,
                )

            try:
                chat_id = int(chat_id)
            except (TypeError, ValueError):
                return Response(
                    {"success": False, "error": "chat_id must be a valid integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            message, participant_ids = MessageServices.create_direct_message(
                user_id=user.id,
                chat_id=chat_id,
                content=content,
                image_content=image,
            )

            # Broadcast to all participants via channel layer (like bell notifications)
            channel_layer = get_channel_layer()
            if channel_layer:
                for pid in participant_ids:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{pid}",
                        {
                            "type": "user_message",
                            "chat_id": chat_id,
                            "message": content,
                            "sender": user.id,
                            "full_name": user.full_name,
                            "timestamp": message.sent_at.isoformat(),
                            "message_id": message.id,
                            "status": message.status,
                            "profile_image": (
                                user.profile_image.url if user.profile_image else None
                            ),
                        },
                    )

            return Response(
                {
                    "success": True,
                    "data": {
                        "id": message.id,
                        "sender": user.id,
                        "full_name": user.full_name,
                        "content": message.content,
                        "image": (
                            message.image_content.url if message.image_content else None
                        ),
                        "timestamp": message.sent_at,
                        "organization": user.primary_organization,
                        "profile_image": (
                            user.profile_image.url if user.profile_image else None
                        ),
                        "status": message.status,
                    },
                }
            )
        except ValidationError as error:
            return Response(
                {"success": False, "error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except APIException:
            logger.exception("Database error while sending a direct message")
            return Response(
                {
                    "success": False,
                    "error": "A database error occurred while sending the message.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # GET unread DM counts per chat for the current user
    @action(detail=False, methods=["get"], url_path="unread-counts")
    @permission_classes([IsAuthenticated])
    def get_unread_counts(self, request):
        try:
            result = ChatServices.get_unread_counts(user_id=request.user.id)
            return Response({"success": True, "data": result})
        except APIException:
            logger.exception("Database error while fetching unread chat counts")
            return Response(
                {
                    "success": False,
                    "error": "A database error occurred while fetching unread counts.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # POST mark a chat as read
    @action(detail=True, methods=["post"], url_path="read")
    @permission_classes([IsAuthenticated])
    def mark_chat_read(self, request, id):
        try:
            message_ids = ChatServices.mark_chat_read(
                chat_id=id,
                user_id=request.user.id,
            )
            return Response(
                {
                    "success": True,
                    "message_ids": message_ids,
                }
            )
        except ValidationError:
            return Response(
                {"success": False, "error": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except APIException:
            logger.exception("Database error while marking chat as read")
            return Response(
                {
                    "success": False,
                    "error": "A database error occurred while marking the "
                    "chat as read.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # GET Group Message
    @action(
        detail=False,
        methods=["get"],
        url_path="group-messages/(?P<group_name>[^/.]+)",
    )
    @permission_classes([IsAuthenticated])
    def get_group_messages(self, request, group_name=None):
        try:
            messages = ChatServices.get_group_messages(group_name=group_name)
            return Response(
                {
                    "messages": [
                        {
                            "id": message.id,
                            "sender": message.user.id,
                            "full_name": message.user.full_name,
                            "content": message.content,
                            "timestamp": message.sent_at,
                            "organization": message.user.primary_organization,
                            "profile_image": (
                                message.user.profile_image.url
                                if message.user.profile_image
                                else None
                            ),
                            "image": message.image.url if message.image else None,
                        }
                        for message in messages
                    ]
                }
            )
        except APIException:
            logger.exception("Database error while fetching group messages")
            return Response(
                {
                    "success": False,
                    "error": "A database error occurred while fetching group messages.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # POST Group Message
    @action(detail=False, methods=["post"], url_path="group-messages")
    @permission_classes([IsAuthenticated])
    def create_group_message(self, request):
        user = request.user
        group_name = request.data.get("group_name")
        content = request.data.get("content", "")
        image = request.FILES.get("image", None)

        if not group_name:
            return Response(
                {"success": False, "error": "group_name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            msg = ChatServices.create_group_message(
                user=user,
                group_name=group_name,
                content=content,
                image=image,
            )
            return Response(
                {
                    "success": True,
                    "data": {
                        "id": msg.id,
                        "sender": msg.user.id,
                        "full_name": msg.user.full_name,
                        "content": msg.content,
                        "image": msg.image.url if msg.image else None,
                        "timestamp": msg.sent_at,
                        "organization": msg.user.primary_organization,
                        "profile_image": (
                            msg.user.profile_image.url
                            if msg.user.profile_image
                            else None
                        ),
                    },
                }
            )
        except APIException:
            logger.exception("Database error while creating group message")
            return Response(
                {
                    "success": False,
                    "error": (
                        "A database error occurred while creating a group message."
                    ),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # DELETE Group Message
    @action(detail=True, methods=["delete"], url_path="group-messages")
    @permission_classes([IsAuthenticated])
    def delete_group_message(self, request, id):
        try:
            ChatServices.delete_group_message(message_id=id)
            return Response(
                {"message": "Message Deleted Successfully", "success": True},
                status=status.HTTP_200_OK,
            )
        except ValidationError:
            return Response(
                {"message": "Message not found", "success": False},
                status=status.HTTP_404_NOT_FOUND,
            )
        except APIException:
            logger.exception("Database error while deleting group message")
            return Response(
                {
                    "success": False,
                    "error": (
                        "A database error occurred while deleting a group message."
                    ),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # PATCH Group Message
    @action(detail=True, methods=["patch"], url_path="group-messages")
    @permission_classes([IsAuthenticated])
    def update_group_message(self, request, id):
        try:
            content = request.data.get("content")
            ChatServices.update_group_message(message_id=id, content=content)
            return Response(
                {"message": "Message updated successfully", "success": True},
                status=status.HTTP_200_OK,
            )
        except ValidationError:
            return Response(
                {"message": "Message not found", "success": False},
                status=status.HTTP_404_NOT_FOUND,
            )
        except APIException:
            logger.exception("Database error while updating group message")
            return Response(
                {
                    "success": False,
                    "error": (
                        "A database error occurred while updating a group message."
                    ),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MessageViewSet(viewsets.ModelViewSet):
    # POST (Create) message
    @action(detail=False, methods=["post"], url_path="messages")
    def create_message_request(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = MessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "message": str(serializer.errors),
                    "success": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        created_message_data = CreateMessageData(
            user_id=request.user.id,
            chat_id=validated_data["chat"].id,
            content=validated_data["content"],
            image_content=validated_data.get("image_content", None),
            sent_at=timezone.now(),
        )

        try:
            message = MessageServices.create_message(created_message_data)
            response_serializer = MessageSerializer(message)

            return Response(
                {
                    "message": "Message sent successfully",
                    "success": True,
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {
                    "message": str(e),
                    "success": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # DELETE message
    @action(detail=True, methods=["delete"], url_path="messages")
    @permission_classes([IsAuthenticated])
    def delete_message_request(self, request, id):
        message_id = id

        try:
            MessageServices.delete_message(message_id)

            return Response(
                {
                    "message": "Message Deleted Successfully",
                    "success": True,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            # If services method returns an error, return an error Response
            return Response(
                {
                    "message": str(e),
                    "success": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    # PATCH (uppdate) message
    @action(detail=True, methods=["patch"], url_path="messages")
    @permission_classes([IsAuthenticated])
    def update_message_request(self, request, id):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        message_id = id

        # Use a serializer to check if the data is valid
        serializer = OptionalMessageSerializer(data=request.data)

        # If the data is NOT valid return with message serializers errors
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If here, the data was validated
        validated_data = serializer.validated_data

        # Convert the data to the UpdateMessageData type
        update_message_data = UpdateMessageData(
            id=id,
            user_id=validated_data.get("user_id"),
            chat_id=validated_data.get("chat_id"),
            content=validated_data.get("content"),
            image_content=validated_data.get("image_content"),
            sent_at=validated_data.get("sent_at"),
            is_edited=validated_data.get("is_edited"),
        )

        try:
            is_edited = MessageServices.update_message(message_id, update_message_data)

            return Response(
                {
                    "message": "Message updated successfully",
                    "success": True,
                    "is_edited": is_edited,
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            # Return an error if the services method returns an error
            return Response(
                {"message": str(e), "success": False},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["patch"])
    def update_status(self, request, id):
        message = MessageServices.get_message(id)

        serializer = MessageStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        status = serializer.validated_data["status"]

        update_data = UpdateMessageData(
            id=message.id,
            status=status,
        )

        MessageServices.update_message(message.id, update_data)

        try:
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"chat_{message.chat_id}",
                {
                    "type": "message_status",
                    "message_id": message.id,
                    "status": status,
                },
            )
        except Exception:
            logger.exception("Failed to broadcast message status update")

        return Response(
            {
                "success": True,
                "message": "Message status updated successfully",
            }
        )

    @action(detail=True, methods=["patch"], url_path="reaction")
    def toggle_reaction_on_message(self, request, id):
        if error := PostViewSet._reaction_request_error(request):
            return error

        reaction_type = request.data["reaction_type"]
        try:
            reaction_created, message_text = (
                ReactionServices.toggle_reaction_on_message(
                    ToggleMessageReactionData(
                        user_id=request.user.id,
                        message_id=int(id),
                        reaction_type=reaction_type,
                    )
                )
            )
            message = MessageServices.get_message(id=int(id))
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if reaction_created:
            PostViewSet._notify_reaction(
                recipient_id=message.user_id,
                actor_id=request.user.id,
                target_id=message.id,
                reaction_type=reaction_type,
            )

        serializer = MessageSerializer(message)
        return Response(
            {"message": message_text, "reactions": serializer.data["reactions"]},
            status=status.HTTP_200_OK,
        )
