from typing import List
from django.core.exceptions import ValidationError
from .daos import ActivityDao
from .types import ActivityWithDescription
from users.models import User
import datetime


HISTORY_TYPE = {"+": "Created", "~": "Updated", "-": "Deleted"}


# Helper function to format field name
def format_field_name(field_name: str) -> str:
    return field_name.replace("_", " ")


# Helper function to create a readable description for each activity
def get_activity_description(activity) -> str:
    model_name = activity.__class__.__name__.replace("Historical", "").lower()

    # Created or deleted → no previous record
    if activity.history_type in ("+", "-"):
        if model_name == "post":
            return (
                f"{HISTORY_TYPE.get(activity.history_type)} a post: "
                f"'{activity.content}'"
            )
        elif model_name == "comment":
            return (
                f"{HISTORY_TYPE.get(activity.history_type)} a comment: "
                f"'{activity.content}'"
            )
        elif model_name == "user":
            return "Welcome to Atria, you've just created an account!"
        else:
            return f"{HISTORY_TYPE.get(activity.history_type)} {model_name}"

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
        ignored_fields = [
            "history_id",
            "history_date",
            "history_type",
            "history_user",
            "date_joined",
            "created_at",
            "last_login",
            "likes",
        ]

        for field in activity._meta.fields:
            name = field.name
            if name in ignored_fields:
                continue
            old = getattr(previous, name)
            new = getattr(activity, name)

            if isinstance(new, datetime.datetime):
                new = new.strftime("%b %-d, %Y at %-I:%M%p")

            if old != new:
                field_label = format_field_name(name)
                if model_name == "comment":
                    changed_fields.append(f"{field_label} to '{new}'")
                elif field_label == "last login":
                    changed_fields.append("You've logged in and started a session")

                elif model_name == "user":
                    changed_fields.append(f"{field_label}")
                else:
                    changed_fields.append(f"{field_label} for {model_name} to '{new}'")

        if changed_fields:
            # If more than 2 fields changed, show first 2 and "+ x more"
            if len(changed_fields) > 2:
                displayed = changed_fields[:2]
                remaining = len(changed_fields) - 2
                joined = ", ".join(displayed)
                return f"Updated {model_name}: {joined} " f"+ {remaining} more..."
            else:
                fields_str = ", ".join(changed_fields)
                return f"Updated {model_name}: {fields_str}"
        else:

            if model_name == "post":

                return "Someone interacted with your post!"
            else:
                return f"Updated {model_name}"

    hist = HISTORY_TYPE.get(activity.history_type, "changed")
    return f"{hist} {model_name}"


class ActivityServices:
    @staticmethod
    def get_user_activities(user_id: int) -> List[ActivityWithDescription]:
        if not user_id:
            raise ValidationError("Invalid user_id")

        if not User.objects.filter(id=user_id).exists():
            raise ValidationError(f"User with id {user_id} does not exist")

        all_activities = ActivityDao.get_user_activities(user_id)

        # Add 'description' via list comprehension for client display
        activities_with_desc = [
            ActivityWithDescription(
                description=get_activity_description(a),
                model=(a.__class__.__name__.replace("Historical", "").lower()),
                activity={
                    f.name: (
                        getattr(a, f.name).id
                        if hasattr(getattr(a, f.name), "id")
                        else getattr(a, f.name)
                    )
                    for f in a._meta.fields
                },
            )
            for a in all_activities
        ]

        return activities_with_desc
