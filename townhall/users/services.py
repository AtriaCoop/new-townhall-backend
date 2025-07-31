import logging
from django.forms import ValidationError
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.db.models.query import QuerySet
import typing

from .models import User
from .types import CreateUserData, UpdateUserData, FilterUserData
from .daos import UserDao

logger = logging.getLogger(__name__)


def _handle_profile_image_update(user, profile_image):
    """Handle profile image update for Cloudinary storage"""
    if profile_image is None:
        return

    if isinstance(profile_image, str):
        user.profile_image = profile_image
    elif hasattr(profile_image, "read"):
        profile_image.seek(0)
        user.profile_image = profile_image
    else:
        raise ValidationError(
            "profile_image must be a string (URL) or file-like object"
        )


def _handle_profile_header_update(user, profile_header):
    """Handle profile header update for Cloudinary storage"""
    if profile_header is None:
        return

    if isinstance(profile_header, str):
        user.profile_header = profile_header
    elif hasattr(profile_header, "read"):
        profile_header.seek(0)
        user.profile_header = profile_header
    else:
        raise ValidationError(
            "profile_header must be a string (URL) or file-like object"
        )


class UserServices:

    def validate_user(email: str, password: str) -> None:
        # Validates the email
        validator = EmailValidator()
        try:
            validator(email)
        except ValidationError:
            raise ValidationError("Invalid email format.")

        # Validates the password
        try:
            validate_password(password)
        except ValidationError as e:
            raise ValidationError(e.messages[0])

        # Prevent emails that are too similar to the password
        if email.lower() in password.lower() or password.lower() in email.lower():
            raise ValidationError("Password is too similar to the email.")

    def create_user(create_user_data: CreateUserData) -> User:
        try:
            if User.objects.filter(email=create_user_data.email).exists():
                raise ValidationError("A User with this email already exists.")
            UserServices.validate_user(
                create_user_data.email, create_user_data.password
            )
            create_user_data.password = make_password(create_user_data.password)
            user = UserDao.create_user(create_user_data=create_user_data)

            return user
        except ValidationError:
            raise

    def get_user(id: int) -> typing.Optional[User]:
        try:
            user = UserDao.get_user(id=id)
            return user
        except User.DoesNotExist:
            raise ValidationError(f"User with the given id: {id}, does not exist.")

    def get_user_all(
        filter_user_data: typing.Optional[FilterUserData] = None,
    ) -> QuerySet[User]:
        if filter_user_data is not None:
            filters = {}
            if filter_user_data.full_name:
                filters["full_name__icontains"] = filter_user_data.full_name
            if filter_user_data.email:
                filters["email__iexact"] = filter_user_data.email

            return UserDao.filter_all_users(filtersDict=filters)
        else:
            return UserDao.get_user_all()

    def update_user(update_user_data: UpdateUserData) -> User:
        try:
            user = User.objects.get(id=update_user_data.id)
        except User.DoesNotExist:
            raise ValidationError(f"User with id {update_user_data.id} does not exist.")

        # Update regular fields
        if update_user_data.full_name is not None:
            user.full_name = update_user_data.full_name

        if update_user_data.email is not None:
            user.email = update_user_data.email

        if update_user_data.pronouns is not None:
            user.pronouns = update_user_data.pronouns

        if update_user_data.title is not None:
            user.title = update_user_data.title

        if update_user_data.primary_organization is not None:
            user.primary_organization = update_user_data.primary_organization

        if update_user_data.other_organizations is not None:
            user.other_organizations = update_user_data.other_organizations

        if update_user_data.other_networks is not None:
            user.other_networks = update_user_data.other_networks

        if update_user_data.about_me is not None:
            user.about_me = update_user_data.about_me

        if update_user_data.skills_interests is not None:
            user.skills_interests = update_user_data.skills_interests

        # Handle image updates
        _handle_profile_image_update(user, update_user_data.profile_image)
        _handle_profile_header_update(user, update_user_data.profile_header)

        try:
            user.save()
            return user
        except Exception as e:
            raise ValidationError(f"Error saving user: {str(e)}")

    def delete_user(id: int) -> None:
        try:
            UserDao.delete_user(user_id=id)
        except User.DoesNotExist:
            raise ValidationError(f"User with the given id: {id}, does not exist.")
