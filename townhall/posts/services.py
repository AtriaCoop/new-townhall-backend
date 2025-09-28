from django.forms import ValidationError
import typing

from .models import Post, ReportedPosts
from .types import CreatePostData, UpdatePostData, CreateCommentData, ReportedPostsData
from .daos import PostDao, CommentDao, ReportedPostsDao

from .profanity import censor_text


class PostServices:
    @staticmethod
    def get_post(id: int) -> typing.Optional[Post]:
        try:
            post = PostDao.get_post(id=id)
            return _mask_post_instance(post)
        except Post.DoesNotExist:
            raise ValidationError(f"Post with the given id: {id}, does not exist.")

    @staticmethod
    def get_all_posts() -> typing.List[Post]:
        posts = PostDao.get_all_posts()
        return _mask_post_list(posts)

    @staticmethod
    def create_post(create_post_data: CreatePostData) -> Post:
        post = PostDao.create_post(post_data=create_post_data)
        return _mask_post_instance(post)

    @staticmethod
    def update_post(id: int, update_post_data: UpdatePostData) -> Post:
        post = PostDao.update_post(id=id, post_data=update_post_data)
        return _mask_post_instance(post)

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


# Masking helpers
def _mask_post_instance(post: Post) -> Post:
    if hasattr(post, "content"):
        post.content = censor_text(post.content)
    return post


def _mask_post_list(posts: typing.Iterable[Post]) -> typing.List[Post]:
    return [_mask_post_instance(post) for post in posts]


class ReportedPostsServices:
    @staticmethod
    def create_reported_post(
        create_reported_post_data: ReportedPostsData,
    ) -> ReportedPosts:

        # A user should only be able to report a post once
        if ReportedPosts.objects.filter(
            user_id=create_reported_post_data.user_id,
            post_id=create_reported_post_data.post_id,
        ).exists():
            raise ValueError("You have already reported this post.")

        reported_post = ReportedPostsDao.create_reported_post(
            create_reported_post_data=create_reported_post_data
        )

        return reported_post
