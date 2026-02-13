import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.forms import ValidationError

from .models import Event
from .serializers import EventSerializer, CreateEventSerializer
from .services import EventServices
from .types import CreateEventData, UpdateEventData

logger = logging.getLogger(__name__)


class EventViewSet(viewsets.GenericViewSet):
    queryset = Event.objects.none()

    @action(detail=False, methods=["get"], url_path="event")
    def get_all_events(self, request):
        try:
            events = EventServices.get_all_events()
            serializer = EventSerializer(
                events, many=True, context={"request": request}
            )
            return Response(
                {"message": "Events fetched successfully", "events": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Failed to fetch events")
            return Response(
                {"error": "An internal error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="event")
    def get_event(self, request, pk=None):
        try:
            event = EventServices.get_event(id=pk)
            serializer = EventSerializer(event, context={"request": request})
            return Response(
                {"message": "Event fetched successfully", "event": serializer.data},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"], url_path="event")
    def create_event(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.is_staff:
            return Response(
                {"error": "Only organizers can create events"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateEventSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = serializer.validated_data
        create_data = CreateEventData(
            admin_id=request.user.id,
            title=validated["title"],
            description=validated.get("description", ""),
            date=validated["date"],
            time=validated["time"],
            location=validated["location"],
        )

        try:
            event = EventServices.create_event(create_data)
            response_serializer = EventSerializer(
                event, context={"request": request}
            )
            return Response(
                {"message": "Event created successfully", "event": response_serializer.data},
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="event")
    def update_event(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if request.user.id != event.admin_id:
            return Response(
                {"error": "Only the event organizer can edit this event"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateEventSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = serializer.validated_data
        update_data = UpdateEventData(
            title=validated.get("title"),
            description=validated.get("description"),
            date=validated.get("date"),
            time=validated.get("time"),
            location=validated.get("location"),
        )

        try:
            updated_event = EventServices.update_event(
                event=event, update_event_data=update_data
            )
            response_serializer = EventSerializer(
                updated_event, context={"request": request}
            )
            return Response(
                {
                    "message": "Event updated successfully",
                    "event": response_serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["delete"], url_path="event")
    def delete_event(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if request.user.id != event.admin_id and not request.user.is_staff:
            return Response(
                {"error": "Only the event admin can delete this event"},
                status=status.HTTP_403_FORBIDDEN,
            )

        EventServices.delete_event(event=event)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="participate")
    def participate(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            event = EventServices.participate(event_id=pk, user_id=request.user.id)
            serializer = EventSerializer(event, context={"request": request})
            return Response(
                {"message": "Successfully enrolled", "event": serializer.data},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="unenroll")
    def unenroll(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            event = EventServices.unenroll(event_id=pk, user_id=request.user.id)
            serializer = EventSerializer(event, context={"request": request})
            return Response(
                {"message": "Successfully unenrolled", "event": serializer.data},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
