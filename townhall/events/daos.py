from .models import Event
from .types import CreateEventData, UpdateEventData


class EventDao:
    @staticmethod
    def get_event(id: int) -> Event:
        return (
            Event.objects.select_related("admin")
            .prefetch_related("participants")
            .get(id=id)
        )

    @staticmethod
    def get_all_events() -> list[Event]:
        return list(
            Event.objects.select_related("admin")
            .prefetch_related("participants")
            .all()
        )

    @staticmethod
    def create_event(event_data: CreateEventData) -> Event:
        event = Event.objects.create(
            admin_id=event_data.admin_id,
            title=event_data.title,
            description=event_data.description,
            date=event_data.date,
            time=event_data.time,
            location=event_data.location,
        )
        return event

    @staticmethod
    def update_event(event: Event, event_data: UpdateEventData) -> Event:
        if event_data.title is not None:
            event.title = event_data.title
        if event_data.description is not None:
            event.description = event_data.description
        if event_data.date is not None:
            event.date = event_data.date
        if event_data.time is not None:
            event.time = event_data.time
        if event_data.location is not None:
            event.location = event_data.location

        event.save()
        return event

    @staticmethod
    def delete_event(event: Event) -> None:
        event.delete()
