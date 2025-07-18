from django.forms import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from .serializers import ChatSerializer, MessageSerializer, CreateChatSerializer
from .services import ChatServices, MessageServices
from .types import CreateChatData, CreateMessageData
from django.utils import timezone
from .models import Chat
from .models import Message
from .models import GroupMessage


class ChatViewSet(viewsets.ModelViewSet):

    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    # GET One Chat
    @action(detail=True, methods=["get"], url_path="chats")
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
    def get_user_chats(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response(
                {"message": "Missing user_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            chats = Chat.objects.filter(participants__id=user_id).distinct()
            serializer = ChatSerializer(chats, many=True)
            return Response(
                {
                    "message": "Chats fetched successfully",
                    "success": True,
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": str(e), "success": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # DELETE Chat
    @action(detail=True, methods=["delete"], url_path="chats")
    def delete_chat_request(self, request, id):
        chat_id = id

        try:
            ChatServices.delete_chat(chat_id)

            return Response(
                {
                    "message": "Chat Deleted Successfully",
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

    # POST (Create) Chat
    @action(detail=False, methods=["post"], url_path="chats")
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
        )

        try:
            chat, created = ChatServices.get_or_create_chat(create_chat_data)
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
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {
                    "message": str(e),
                    "success": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # GET Message
    @action(detail=True, methods=["get"], url_path="messages")
    def get_chat_messages(self, request, id):
        messages = Message.objects.filter(chat_id=id).order_by("sent_at")
        serializer = MessageSerializer(messages, many=True)
        return Response({"messages": serializer.data})

    # POST Message
    @action(detail=False, methods=["post"], url_path="direct-message")
    def create_direct_message(self, request):
        try:
            user = request.user
            chat_id = request.data.get("chat_id")
            content = request.data.get("content", "")
            image = request.FILES.get("image_content", None)

            if not chat_id:
                return Response(
                    {"success": False, "error": "chat_id is required"}, status=400
                )

            message = Message.objects.create(
                user=user, chat_id=chat_id, content=content, image_content=image
            )

            return Response(
                {
                    "success": True,
                    "data": {
                        "sender": message.user.id,
                        "full_name": message.user.full_name,
                        "content": message.content,
                        "image": (
                            message.image_content.url if message.image_content else None
                        ),
                        "timestamp": message.sent_at,
                        "organization": message.user.primary_organization,
                        "profile_image": (
                            message.user.profile_image.url
                            if message.user.profile_image
                            else None
                        ),
                    },
                }
            )
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)

    # GET Group Message
    @action(
        detail=False, methods=["get"], url_path="group-messages/(?P<group_name>[^/.]+)"
    )
    def get_group_messages(self, request, group_name=None):
        msgs = GroupMessage.objects.filter(group_name=group_name).order_by("sent_at")

        return Response(
            {
                "messages": [
                    {
                        "sender": m.user.id,
                        "full_name": m.user.full_name,
                        "content": m.content,
                        "timestamp": m.sent_at,
                        "organization": m.user.primary_organization,
                        "profile_image": (
                            m.user.profile_image.url if m.user.profile_image else None
                        ),
                        "image": m.image.url if m.image else None,
                    }
                    for m in msgs
                ]
            }
        )

    # POST Group Message
    @action(detail=False, methods=["post"], url_path="group-messages")
    def create_group_message(self, request):
        try:
            user = request.user  # You must be using authentication
            group_name = request.data.get("group_name")
            content = request.data.get("content", "")
            image = request.FILES.get("image", None)

            msg = GroupMessage.objects.create(
                user=user, group_name=group_name, content=content, image=image
            )

            return Response(
                {
                    "success": True,
                    "data": {
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
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


class MessageViewSet(viewsets.ModelViewSet):
    # POST (Create) message
    @action(detail=False, methods=["post"], url_path="messages")
    def create_message_request(self, request):
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
            user_id=validated_data["user"].id,
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
