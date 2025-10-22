from typing import List
from django.forms import ValidationError
from .daos import ActivityDao
from .types import ActivityWithDescription
from users.models import User


metadata = {"+": "created", "~": "updated", "-": "deleted"}


# Helper function to format field name
def format_field_name(field_name: str) -> str:
    return field_name.replace("_", " ")


# Helper function to create a formatted description for each activity
def get_activity_description(activity) -> str:
    model_name = activity.__class__.__name__.replace("Historical", "").lower()

    # Created or deleted → no previous record
    if activity.history_type in ("+", "-"):
        if model_name == "post":
            return f"{metadata.get(activity.history_type)} a post: '{activity.content}'"
        elif model_name == "comment":
            return (
                f"{metadata.get(activity.history_type)} a comment on a post by "
                f"{activity.post.user.full_name}"
            )
        else:
            return f"{metadata.get(activity.history_type)} {model_name}"

    # Updated → compare fields with previous version
    if activity.history_type == "~":
        # Get the previous version (ordered by history_date)
        previous_qs = activity.__class__.objects.filter(id=activity.id).order_by(
            "-history_date"
        )

        # Edge case, if updated there should be at least 2 records
        if previous_qs.count() < 2:
            return f"updated {model_name}"
        previous = previous_qs[1]  # the version before this one

        changed_fields = []
        for field in activity._meta.fields:
            name = field.name
            old = getattr(previous, name)
            new = getattr(activity, name)
            if old != new:
                field_label = format_field_name(name)
                changed_fields.append(f"{field_label} to '{new}'")

        if changed_fields:
            return f"updated {', '.join(changed_fields)} for {model_name}"
        else:
            return f"updated {model_name}"

    return f"{metadata.get(activity.history_type, 'changed')} {model_name}"


class ActivityServices:
    @staticmethod
    def get_user_activities(user_id: int) -> List[ActivityWithDescription]:
        if not user_id:
            raise ValidationError("Invalid user_id")

        if not User.objects.filter(id=user_id).exists():
            raise ValidationError(f"User with id {user_id} does not exist")

        all_activities = ActivityDao.get_user_activities(user_id)

        # Add a property 'description' using list comprehension so we can display
        # in the client
        # Use the type we created
        activities_with_desc = [
            ActivityWithDescription(
                activity=activity, description=get_activity_description(activity)
            )
            for activity in all_activities
        ]

        return activities_with_desc
