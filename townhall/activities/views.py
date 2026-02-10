from django.core.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from .services import ActivityServices
from .serializers import ActivitySerializer


class ActivityViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="")
    def get_user_activities(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user_id = request.user.id

        try:
            activities = ActivityServices.get_user_activities(user_id)
            serialized = ActivitySerializer(activities, many=True)

            return Response(
                {
                    "message": "Here are the user's activity logs",
                    "success": True,
                    "data": serialized.data,
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # fallback for unexpected errors
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
