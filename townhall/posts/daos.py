import re
import typing

from django.db.models import Count
from django.forms import ValidationError
from django.db import IntegrityError
from .models import Post, Comment, ReportedPost, Reaction, Tag
from .types import (
    CreatePostData,
    UpdatePostData,
    CreateCommentData,
    UpdateCommentData,
    ReportedPostData,
    ToggleReactionData,
)


class PostDao:

    def get_post(id: int) -> typing.Optional[Post]:
        return Post.objects.prefetch_related('tags').get(id=id)

    def get_all_posts(
        offset: int, limit: int, tag_names: list[str] | None = None
    ) -> tuple[typing.List[Post], int]:
        """Return recent posts paginated with total count, optionally filtered by tags."""
        qs = Post.objects.prefetch_related('tags').order_by("-pinned", "-created_at")
        if tag_names:
            qs = qs.filter(tags__name__in=tag_names).distinct()
        total_count = qs.count()
        items = list(qs[offset : offset + limit])
        return items, total_count

    def get_trending_tags(limit: int = 10) -> list[dict]:
        """Return tags sorted by post usage count."""
        tags = (
            Tag.objects.annotate(post_count=Count("posts", distinct=True))
            .filter(post_count__gte=2)
            .order_by("-post_count")[:limit]
        )
        return [{"name": t.name, "count": t.post_count} for t in tags]

    def create_post(post_data: CreatePostData) -> Post:
        post = Post.objects.create(
            user_id=post_data.user_id,
            content=post_data.content,
            created_at=post_data.created_at,
            image=post_data.image,
            pinned=post_data.pinned,
            anonymous=post_data.anonymous,
        )

        tag_objects = PostDao._create_tag_objects(post_data.tags)
        post.tags.set(tag_objects)

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
        if post_data.pinned is not None:
            post.pinned = post_data.pinned

        tag_objects = PostDao._create_tag_objects(post_data.tags)
        post.tags.set(tag_objects)

        post.save()

        return post

    def delete_post(post_id):
        try:
            post = Post.objects.get(id=post_id)
            post.delete()
        except Post.DoesNotExist:
            raise ValueError(f"Post with ID {post_id} does not exist.")

    def _create_tag_objects(tags: list[str]) -> list[Tag]:
        """Convert tag strings to Tag objects, normalizing and deduplicating."""
        tag_objects = []
        if tags is not None:
            seen = set()
            for tag_name in tags[:5]:  # hard cap at 5
                clean = re.sub(r"[^a-z0-9-]", "", tag_name.strip().lower())
                if len(clean) < 2 or len(clean) > 20:
                    continue
                if clean in seen:
                    continue
                seen.add(clean)
                tag_obj, _ = Tag.objects.get_or_create(name=clean)
                tag_objects.append(tag_obj)
        return tag_objects


class CommentDao:

    def get_comment(id: int) -> typing.Optional[Comment]:
        return Comment.objects.get(id=id)

    def create_comment(create_comment_data: CreateCommentData) -> None:
        comment = Comment.objects.create(
            user_id=create_comment_data.user_id,
            post_id=create_comment_data.post_id,
            content=create_comment_data.content,
            created_at=create_comment_data.created_at,
        )

        return comment

    def update_comment(id: int, update_content_data: UpdateCommentData) -> Comment:
        try:
            comment = Comment.objects.get(id=id)
        except Comment.DoesNotExist:
            msg = f"Comment with ID {id} does not exist."
            raise ValidationError(msg)

        if update_content_data.content is not None:
            comment.content = update_content_data.content

        comment.save()
        return comment


class ReportedPostDao:
    @staticmethod
    def create_reported_post(
        create_reported_post_data: ReportedPostData,
    ) -> ReportedPost:

        try:
            reported_post = ReportedPost.objects.create(
                user_id=create_reported_post_data.user_id,
                post_id=create_reported_post_data.post_id,
                created_at=create_reported_post_data.created_at,
            )
        except IntegrityError:
            raise IntegrityError("User already reported this post")

        return reported_post


class ReactionDao:
    @staticmethod
    def get_reaction(
        post_id: int, user_id: int, reaction_type: str
    ) -> typing.Optional[Reaction]:
        """Get an existing reaction if it exists."""
        try:
            return Reaction.objects.get(
                post_id=post_id, user_id=user_id, reaction_type=reaction_type
            )
        except Reaction.DoesNotExist:
            return None

    @staticmethod
    def create_reaction(reaction_data: ToggleReactionData) -> Reaction:
        """Create a new reaction."""
        return Reaction.objects.create(
            post_id=reaction_data.post_id,
            user_id=reaction_data.user_id,
            reaction_type=reaction_data.reaction_type,
        )

    @staticmethod
    def delete_reaction(reaction: Reaction) -> None:
        """Delete a reaction."""
        reaction.delete()
