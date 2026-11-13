from django.forms import ValidationError

from events.serializers import ShareEventSearializer
from posts.services import PostServices
from posts.types import CreatePostData
from .models import Event
from .types import CreateEventData, UpdateEventData
from .daos import EventDao


class EventServices:
    @staticmethod
    def get_event(id: int) -> Event:
        try:
            return EventDao.get_event(id=id)
        except Event.DoesNotExist:
            raise ValidationError(f"Event with id {id} does not exist.")

    @staticmethod
    def get_all_events() -> list[Event]:
        return EventDao.get_all_events()

    @staticmethod
    def create_event(create_event_data: CreateEventData) -> Event:
        return EventDao.create_event(event_data=create_event_data)

    @staticmethod
    def update_event(event: Event, update_event_data: UpdateEventData) -> Event:
        return EventDao.update_event(event=event, event_data=update_event_data)

    @staticmethod
    def delete_event(event: Event) -> None:
        EventDao.delete_event(event=event)

    @staticmethod
    def participate(event_id: int, user_id: int) -> Event:
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise ValidationError(f"Event with id {event_id} does not exist.")

        event.participants.add(user_id)
        return EventDao.get_event(id=event_id)

    @staticmethod
    def unenroll(event_id: int, user_id: int) -> Event:
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise ValidationError(f"Event with id {event_id} does not exist.")

        event.participants.remove(user_id)
        return EventDao.get_event(id=event_id)

    @staticmethod
    def create_event_post(event: Event, request) -> Event:
        if event.post:
            raise ValidationError("Event post already exists.")

        serializer = ShareEventSearializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_post_data = CreatePostData(
            user_id=event.admin.id,
            content=(
                f"Join us for the event '{event.title}' "
                f"on {event.date} at {event.time} "
                f"in {event.location}."
            ),
            created_at=event.created_at,
            images=[],
            pinned=False,
            tags=["event"],
            anonymous=False,
        )

        try:
            post = PostServices.create_post(create_post_data=create_post_data)
            event = EventDao.update_event(
                event=event, event_data=UpdateEventData(post=post)
            )
            return event
        except Exception as e:
            raise ValidationError(f"Error occurred while creating event post: {str(e)}")
