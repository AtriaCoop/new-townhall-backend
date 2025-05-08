from django.db.models.query import QuerySet
import typing

from .models import User
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
            email=create_user_data.email,
            password=create_user_data.password
        )

        return user

    @staticmethod
    def delete_user(user_id: int) -> None:
        User.objects.get(id=user_id).delete()

    def filter_all_users(filtersDict) -> QuerySet[User]:
        return User.objects.filter(**filtersDict)
