from django.forms import ValidationError
import typing

from .models import Post
from .types import (
    CreatePostData,
    UpdatePostData,
    CreateCommentData
)
from .daos import PostDao, CommentDao


class PostServices:
    @staticmethod
    def get_post(id: int) -> typing.Optional[Post]:
        try:
            post = PostDao.get_post(id=id)
            return post
        except Post.DoesNotExist:
            raise ValidationError(f"Post with the given id: {id}, does not exist.")

    @staticmethod
    def get_all_posts() -> typing.List[Post]:
        return PostDao.get_all_posts()

    @staticmethod
    def create_post(create_post_data: CreatePostData) -> Post:
        post = PostDao.create_post(post_data=create_post_data)
        return post

    @staticmethod
    def update_post(id: int, update_post_data: UpdatePostData) -> Post:
        post = PostDao.update_post(id=id, post_data=update_post_data)
        return post

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
        return comment