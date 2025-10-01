from django.forms import ValidationError
import typing

from .models import Post, ReportedPost, Comment
from .types import (
    CreatePostData,
    UpdatePostData,
    CreateCommentData,
    ReportedPostData,
    UpdateCommentData,
)
from .daos import PostDao, CommentDao, ReportedPostDao
from users.models import User
from .profanity import censor_text


class PostServices:
    @staticmethod
    def get_post(id: int) -> typing.Optional[Post]:
        try:
            post = PostDao.get_post(id=id)
            return _mask_content_instance(post)
        except Post.DoesNotExist:
            raise ValidationError(f"Post with the given id: {id}, does not exist.")

    @staticmethod
    def get_all_posts() -> typing.List[Post]:
        posts = PostDao.get_all_posts()
        return _mask_content_list(posts)

    @staticmethod
    def create_post(create_post_data: CreatePostData) -> Post:
        post = PostDao.create_post(post_data=create_post_data)
        return _mask_content_instance(post)

    @staticmethod
    def update_post(id: int, update_post_data: UpdatePostData) -> Post:
        post = PostDao.update_post(id=id, post_data=update_post_data)
        return _mask_content_instance(post)

    @staticmethod
    def delete_post(post_id: int) -> None:
        try:
            PostDao.delete_post(post_id)
        except ValueError as e:
            raise ValidationError(str(e))


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
            raise ValueError("You have already reported this post.")

        reported_post = ReportedPostDao.create_reported_post(
            create_reported_post_data=create_reported_post_data
        )

        return reported_post
