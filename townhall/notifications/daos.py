import typing
from .models import Notification
from .types import CreateNotificationData


class NotificationDao:
    @staticmethod
    def create_notification(data: CreateNotificationData) -> Notification:
        return Notification.objects.create(
            recipient_id=data.recipient_id,
            actor_id=data.actor_id,
            notification_type=data.notification_type,
            target_id=data.target_id,
            detail=data.detail,
        )

    @staticmethod
    def get_notifications(
        user_id: int, limit: int = 30
    ) -> typing.List[Notification]:
        return list(
            Notification.objects.filter(recipient_id=user_id)
            .select_related("actor")[:limit]
        )

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        return Notification.objects.filter(
            recipient_id=user_id, is_read=False
        ).count()

    @staticmethod
    def mark_all_read(user_id: int) -> int:
        return Notification.objects.filter(
            recipient_id=user_id, is_read=False
        ).update(is_read=True)

    @staticmethod
    def mark_read(notification_id: int, user_id: int) -> bool:
        updated = Notification.objects.filter(
            id=notification_id, recipient_id=user_id
        ).update(is_read=True)
        return updated > 0
