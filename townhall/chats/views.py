from django.forms import ValidationError

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response

from .services import ChatServices, MessageServices
from .serializers import ChatSerializer, MessageSerializer
from .types import CreateChatData, CreateMessageData
from django.utils import timezone


class ChatViewSet(viewsets.ModelViewSet):
    # GET One Chat
    @action(detail=True, methods=["get"], url_path="chats")
    def get_chat_request(self, request, id):
        chat_id = id

        try:
            chat = ChatServices.get_chat(chat_id)
            response_serializer = ChatSerializer(chat)

            return Response(
                {
                    "message": "Chat Retreived Successfully",
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
        serializer = ChatSerializer(data=request.data)

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
            chat = ChatServices.create_chat(create_chat_data)
            response_serializer = ChatSerializer(chat)

            return Response(
                {
                    "message": "Chat Created Successfully",
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
