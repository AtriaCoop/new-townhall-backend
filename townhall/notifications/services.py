import typing
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from .types import CreateNotificationData
from .daos import NotificationDao


class NotificationServices:
    @staticmethod
    def get_notifications(
        user_id: int, limit: int = 30
    ) -> typing.List[Notification]:
        return NotificationDao.get_notifications(user_id, limit)

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        return NotificationDao.get_unread_count(user_id)

    @staticmethod
    def mark_all_read(user_id: int) -> int:
        return NotificationDao.mark_all_read(user_id)

    @staticmethod
    def mark_read(notification_id: int, user_id: int) -> bool:
        return NotificationDao.mark_read(notification_id, user_id)

    @staticmethod
    def create_and_push(data: CreateNotificationData) -> typing.Optional[Notification]:
        """
        Create a notification in the database and push it
        to the recipient's WebSocket channel in real time.

        Returns None if the actor is the same as the recipient.
        """
        if data.actor_id is not None and data.actor_id == data.recipient_id:
            return None

        notification = NotificationDao.create_notification(data)

        actor_obj = None
        if notification.actor:
            actor_obj = {
                "id": notification.actor_id,
                "full_name": notification.actor.full_name or "",
                "profile_image": notification.actor.profile_image.url if notification.actor.profile_image else "",
            }

        payload = {
            "id": notification.id,
            "notification_type": notification.notification_type,
            "actor": actor_obj,
            "target_id": notification.target_id,
            "detail": notification.detail,
            "is_read": False,
            "created_at": str(notification.created_at),
        }

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"user_{data.recipient_id}",
                {
                    "type": "notification_push",
                    "notification": payload,
                },
            )

        return notification
