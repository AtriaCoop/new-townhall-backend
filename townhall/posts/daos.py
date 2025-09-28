import typing

from django.forms import ValidationError
from django.db import IntegrityError
from .models import Post, Comment, ReportedPosts
from .types import CreatePostData, UpdatePostData, CreateCommentData, ReportedPostsData
from users.models import User


class PostDao:

    def get_post(id: int) -> typing.Optional[Post]:
        return Post.objects.get(id=id)

    def get_all_posts() -> typing.List[Post]:
        return Post.objects.all()

    def create_post(post_data: CreatePostData) -> Post:
        print("Image type:", type(post_data.image))
        print("Image value:", post_data.image)

        post = Post.objects.create(
            user_id=post_data.user_id,
            content=post_data.content,
            created_at=post_data.created_at,
            image=post_data.image,
        )

        return post

    def update_post(id: int, post_data: UpdatePostData) -> Post:
        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            raise ValidationError(f"Post with ID {id} does not exist.")

        if post_data.content is not None:
            post.content = post_data.content
        if post_data.image is not None:
            post.image = post_data.image

        post.save()

        return post

    def delete_post(post_id):
        try:
            post = Post.objects.get(id=post_id)
            post.delete()
        except Post.DoesNotExist:
            raise ValueError(f"Post with ID {post_id} does not exist.")


class CommentDao:

    def create_comment(create_comment_data: CreateCommentData) -> None:
        comment = Comment.objects.create(
            user_id=create_comment_data.user_id,
            post_id=create_comment_data.post_id,
            content=create_comment_data.content,
            created_at=create_comment_data.created_at,
        )

        return comment


class ReportedPostsDao:
    @staticmethod
    def create_reported_post(reported_posts_data: ReportedPostsData) -> ReportedPosts:

        existing_post = Post.objects.get(id=reported_posts_data.post_id)
        if not existing_post:
            raise ValidationError(
                f"Post with ID {reported_posts_data.post_id} does not exist."
            )

        existing_user = User.objects.get(id=reported_posts_data.user_id)
        if not existing_user:
            raise ValidationError(
                f"User with ID {reported_posts_data.user_id} does not exist."
            )

        try:
            reported_post = ReportedPosts.objects.create(
                user_id=reported_posts_data.user_id,
                post_id=reported_posts_data.post_id,
                created_at=reported_posts_data.created_at,
            )
        except IntegrityError as e:
            raise ValueError(f"Database constraint issues: {e}")

        return reported_post
