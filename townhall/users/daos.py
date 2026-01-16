from django.db.models.query import QuerySet
import typing
from .models import User
from .models import Tag, Report
from .types import CreateUserData, CreateReportData
from django.db.models import Q, Case, When, Value, IntegerField
from django.db.models.functions import Lower


class UserDao:

    @staticmethod
    def get_user_all() -> typing.List[User]:
        return User.objects.all()

    @staticmethod
    def get_user(id: int) -> typing.Optional[User]:
        return User.objects.get(id=id)

    @staticmethod
    def create_user(create_user_data: CreateUserData) -> User:
        user = User.objects.create(
            email=create_user_data.email, password=create_user_data.password
        )

        return user

    @staticmethod
    def delete_user(user_id: int) -> None:
        User.objects.get(id=user_id).delete()

    @staticmethod
    def filter_all_users(filtersDict) -> QuerySet[User]:
        return User.objects.filter(**filtersDict)

    @staticmethod
    def update_user_tags(user_id: int, tag_names: typing.List[str]) -> bool:
        """
        Sets the user's tags to the provided list of tag names.
        Returns True if successful, False if user does not exist.
        """
        try:
            user = User.objects.get(id=user_id)
            tags = Tag.objects.filter(name__in=tag_names)
            user.tags.set(tags)
            return True
        except User.DoesNotExist:
            return False

    @staticmethod
    def get_users_by_tags(tag_names: list[str]) -> QuerySet[User]:
        """
        Returns a QuerySet of users associated with any of the given tag names.
        """
        return User.objects.filter(tags__name__in=tag_names).distinct()

    def update_receive_emails(user_id: int, receive_emails: bool) -> bool:
        try:
            user = User.objects.get(id=user_id)
            user.receive_emails = receive_emails
            user.save()
            return True
        except User.DoesNotExist:
            return False

    @staticmethod
    def get_tags_given_prefix(prefix: str) -> QuerySet[Tag]:
        return Tag.objects.filter(name__istartswith=prefix)

    def get_all_tags() -> QuerySet[Tag]:
        return Tag.objects.all()

    def get_tags_for_user(user_id: int) -> QuerySet[Tag]:
        user = User.objects.get(id=user_id)
        return list(user.tags.values_list("name", flat=True))

    @staticmethod
    def search_users(query: str) -> QuerySet[User]:

        return (
            # Use annotate() to temporarily create a field we can use to
            # compare and rank in the QuerySet
            User.objects.annotate(
                full_name_lowercase=Lower("full_name"),
                # Give ranking scores based on if exact match, starts with, or contains
                rank=Case(
                    When(full_name_lowercase=query, then=Value(3)),
                    When(full_name_lowercase__startswith=query, then=Value(2)),
                    When(full_name_lowercase__icontains=query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                # Filter out results with no matches
            ).filter(Q(rank__gt=0))
            # Limit so we get maximum 15 results
            .order_by("-rank", "full_name")[:15]
        )


class ReportDao:

    @staticmethod
    def create_report(report_data: CreateReportData) -> Report:
        report = Report.objects.create(
            user_id=report_data.user_id,
            content=report_data.content,
            created_at=report_data.created_at,
        )

        return report

    @staticmethod
    def get_report(id: int) -> typing.Optional[Report]:
        return Report.objects.get(id=id)
