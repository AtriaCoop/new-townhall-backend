from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .services import NotificationServices
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.GenericViewSet):

    @action(detail=False, methods=["get"], url_path="notifications")
    def get_notifications(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        notifications = NotificationServices.get_notifications(request.user.id)
        serializer = NotificationSerializer(notifications, many=True)
        unread_count = NotificationServices.get_unread_count(request.user.id)

        return Response(
            {
                "notifications": serializer.data,
                "unread_count": unread_count,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="notifications/unread-count")
    def unread_count(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        count = NotificationServices.get_unread_count(request.user.id)
        return Response(
            {"unread_count": count},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="notifications/mark-all-read")
    def mark_all_read(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        updated = NotificationServices.mark_all_read(request.user.id)
        return Response(
            {"message": f"Marked {updated} notifications as read"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="notifications/mark-read")
    def mark_read(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        success = NotificationServices.mark_read(
            notification_id=pk, user_id=request.user.id
        )
        if success:
            return Response(
                {"message": "Notification marked as read"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Notification not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
