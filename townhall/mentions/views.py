import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from mentions.serializers import MentionSerializer

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
            return Response(
                {
                    "data": {
                        "post_id": validated_data["post"].id,
                        "mentioned_user_id": validated_data["mentioned_user"].id,
                    }
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )
