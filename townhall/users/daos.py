from django.db.models.query import QuerySet
import typing

from .models import User
from .models import Tag
from .types import CreateUserData


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
    def get_tags_given_prefix(prefix: str) -> typing.List[Tag]:
        return Tag.objects.filter(name__istartswith=prefix)

    def get_all_tags() -> QuerySet[Tag]:
        return Tag.objects.all()

    def get_tags_for_user(user_id: int) -> typing.List[str]:
        try:
            user = User.objects.get(id=user_id)
            return list(user.tags.values_list("name", flat=True))
        except User.DoesNotExist:
            return []
