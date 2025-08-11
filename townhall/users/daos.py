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
        if not tag_names:
            return True
        try:
            user = User.objects.get(id=user_id)
            tags = Tag.objects.filter(name__in=tag_names)
            if not tags.exists():
                return True  # No changes made if no tags found
            user.tags.add(*tags)
            return True
        except User.DoesNotExist:
            return False

    @staticmethod
    def delete_tag_from_user(user_id: int, tag_names: typing.List[str]) -> bool:
        """
        Deletes the the specified tags from the specified user.
        Returns True if successful, False if user does not exist.
        """
        if not tag_names:
            return True
        try:
            user = User.objects.get(id=user_id)
            tags = Tag.objects.filter(name__in=tag_names)
            if not tags.exists():
                return True  # No changes made if no tags found
            user.tags.remove(*tags)
            return True
        except User.DoesNotExist:
            return False
