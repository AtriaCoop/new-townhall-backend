import logging

from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from mentions.serializers import MentionSerializer
from .services import MentionServices

from .types import CreateMentionData

logger = logging.getLogger(__name__)


class MentionViewSet(viewsets.ModelViewSet):

    @action(detail=False, methods=["post"], url_path="mention_users")
    def mention_users(self, request):

        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = MentionSerializer(data=request.data)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            create_mention_data = CreateMentionData(
                post_id=validated_data["post"].id,
                mentioned_user_ids=[
                    user.id for user in validated_data["mentioned_user_ids"]
                ],
            )

            try:
                MentionServices.create_mentions(create_mention_data)

                return Response(
                    {"message": "Mentions created successfully"},
                    status=status.HTTP_201_CREATED,
                )
            except ValidationError as e:
                return Response(
                    {"message": str(e), "success": False},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )
