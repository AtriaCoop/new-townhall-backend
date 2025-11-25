from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.forms import ValidationError
import typing

from .models import Post, ReportedPost, Comment, Reaction, Tag
from .types import (
    CreatePostData,
    UpdatePostData,
    CreateCommentData,
    ReportedPostData,
    UpdateCommentData,
    ToggleReactionData,
)
from .daos import PostDao, CommentDao, ReportedPostDao, ReactionDao
from users.models import User
from .profanity import censor_text, _CENSOR_RE


class PostServices:
    MAX_TAG_LENGTH = 50

    @staticmethod
    def get_post(id: int) -> typing.Optional[Post]:
        try:
            post = PostDao.get_post(id=id)
            return _mask_content_instance(post)
        except Post.DoesNotExist:
            raise ValidationError(f"Post with the given id: {id}, does not exist.")

    @staticmethod
    def get_all_posts(page: int = 1, limit: int = 10) -> tuple[typing.List[Post], int]:
        """Return a paginated list of posts for a given page and limit.
        Also returns total number of pages based on limit."""
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit

        posts, total_count = PostDao.get_all_posts(offset, limit)
        total_pages = (total_count + limit - 1) // limit
        return _mask_content_list(posts), total_pages

    @staticmethod
    def create_post(create_post_data: CreatePostData) -> Post:

        user = User.objects.get(id=create_post_data.user_id)
        if not user.is_staff and create_post_data.pinned:
            raise PermissionDenied("You are not authorized to pin posts.")

        # Create the post
        post = PostDao.create_post(post_data=create_post_data)

        # Assign tags after creating the post
        tag_objects = PostServices._validate_and_get_tags(create_post_data.tags)
        if tag_objects:
            post.tags.set(tag_objects)

        return _mask_content_instance(post)

    @staticmethod
    def update_post(id: int, update_post_data: UpdatePostData) -> Post:

        user = User.objects.get(id=update_post_data.user_id)
        if not user.is_staff and update_post_data.pinned is not None:
            raise PermissionDenied("You are not authorized to pin posts.")

        # Update the post
        post = PostDao.update_post(id=id, post_data=update_post_data)

        # Validate and Set tags if provided
        tag_objects = PostServices._validate_and_get_tags(update_post_data.tags)
        if tag_objects:
            post.tags.set(tag_objects)
        elif update_post_data.tags == []:
            post.tags.clear()

        return _mask_content_instance(post)

    @staticmethod
    def delete_post(post_id: int) -> None:
        try:
            PostDao.delete_post(post_id)
        except ValueError as e:
            raise ValidationError(str(e))

    # Tag validator helper
    @staticmethod
    def _validate_and_get_tags(tags: list[str] | None) -> list[Tag]:
        """
        Validate tag lengths and get or create Tag objects.
        Returns a list of Tag objects. If tags is None, returns an empty list.
        """
        tag_objects = []

        if tags is not None:  # None = leave unchanged
            for tag_name in tags:
                # 1. Check max length
                if len(tag_name) > PostServices.MAX_TAG_LENGTH:
                    raise ValidationError(
                        (
                            f"Tag '{tag_name}' exceeds the maximum length of "
                            f"{PostServices.MAX_TAG_LENGTH} characters."
                        )
                    )

                # 2. Check for profanity
                if _CENSOR_RE.search(tag_name):
                    raise ValidationError(
                        f"Tag '{tag_name}' contains inappropriate language."
                    )

                # 3. Get or Create tag object
                tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
                tag_objects.append(tag_obj)

        return tag_objects


class CommentServices:
    @staticmethod
    def create_comment(create_comment_data: CreateCommentData) -> None:
        comment = CommentDao.create_comment(create_comment_data=create_comment_data)
        if hasattr(comment, "content"):
            comment.content = censor_text(comment.content)
        return comment

    @staticmethod
    def update_comment(id: int, update_comment_data: UpdateCommentData) -> Comment:
        comment = CommentDao.update_comment(id, update_comment_data)
        return _mask_content_instance(comment)


# Masking helpers
def _mask_content_instance(object) -> typing.Any:
    if hasattr(object, "content"):
        object.content = censor_text(object.content)
    return object


def _mask_content_list(objects: typing.Iterable) -> typing.List:
    return [_mask_content_instance(object) for object in objects]


class ReportedPostServices:
    @staticmethod
    def create_reported_post(
        create_reported_post_data: ReportedPostData,
    ) -> ReportedPost:

        # handle invlaid inputs
        if (
            not create_reported_post_data.user_id
            or not create_reported_post_data.post_id
        ):
            raise ValidationError("Invalid user_id or post_id")

        # Check if the user exists
        if not User.objects.filter(id=create_reported_post_data.user_id).exists():
            raise ValidationError(
                f"User with id {create_reported_post_data.user_id} doesn't exist."
            )

        # Check if the post exists
        if not Post.objects.filter(id=create_reported_post_data.post_id).exists():
            raise ValidationError(
                f"Post with id {create_reported_post_data.post_id} doesn't exist."
            )

        # A user should only be able to report a post once
        if ReportedPost.objects.filter(
            user_id=create_reported_post_data.user_id,
            post_id=create_reported_post_data.post_id,
        ).exists():
            raise IntegrityError("You have already reported this post.")

        reported_post = ReportedPostDao.create_reported_post(
            create_reported_post_data=create_reported_post_data
        )

        return reported_post


class ReactionServices:
    @staticmethod
    def toggle_reaction(reaction_data: ToggleReactionData) -> typing.Tuple[bool, str]:
        # Validate that the post exists
        try:
            PostDao.get_post(id=reaction_data.post_id)
        except Post.DoesNotExist:
            raise ValidationError(
                f"Post with id {reaction_data.post_id} does not exist."
            )

        # Validate that the user exists
        if not User.objects.filter(id=reaction_data.user_id).exists():
            raise ValidationError(
                f"User with id {reaction_data.user_id} does not exist."
            )

        # Validate reaction type
        valid_reactions = [choice[0] for choice in Reaction.Reaction_Choices]
        if reaction_data.reaction_type not in valid_reactions:
            raise ValidationError(
                f"Invalid reaction type. Must be one of: {', '.join(valid_reactions)}"
            )

        # Check if reaction already exists
        existing_reaction = ReactionDao.get_reaction(
            post_id=reaction_data.post_id,
            user_id=reaction_data.user_id,
            reaction_type=reaction_data.reaction_type,
        )

        if existing_reaction:
            # Remove the reaction
            ReactionDao.delete_reaction(existing_reaction)
            return (False, f"Removed {reaction_data.reaction_type} reaction")
        else:
            # Add the reaction
            try:
                ReactionDao.create_reaction(reaction_data)
                return (True, f"Added {reaction_data.reaction_type} reaction")
            except IntegrityError:
                # Handle race condition where reaction was added between
                # check and create. Try to get it again - if it exists now,
                # treat as if it was already there
                existing_reaction = ReactionDao.get_reaction(
                    post_id=reaction_data.post_id,
                    user_id=reaction_data.user_id,
                    reaction_type=reaction_data.reaction_type,
                )
                if existing_reaction:
                    # Reaction was added by another request, remove it
                    ReactionDao.delete_reaction(existing_reaction)
                    return (
                        False,
                        f"Removed {reaction_data.reaction_type} reaction",
                    )
                else:
                    raise ValidationError(
                        "Failed to create reaction due to database constraint"
                    )
