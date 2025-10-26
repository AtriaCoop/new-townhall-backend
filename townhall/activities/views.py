from django.forms import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from .services import ActivityServices
from .serializers import ActivitySerializer


class ActivityViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="")
    def get_user_activities(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response(
                {"message": "Missing user_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # fallback for unexpected errors
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
