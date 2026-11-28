from django.core.exceptions import ValidationError

from .types import CreateMentionData

from .daos import MentionDao

from posts.models import Post
from users.models import User


class MentionServices:
    @staticmethod
    def create_mentions(data: CreateMentionData):
        mentioned_user_ids = set(data.mentioned_user_ids)
        if not Post.objects.filter(pk=data.post_id).exists() or (
            User.objects.filter(pk__in=mentioned_user_ids).count()
            != len(mentioned_user_ids)
        ):
            raise ValidationError(
                "The post or one or more mentioned users do not exist."
            )

        try:
            MentionDao.create_mentions(data)
        except (Post.DoesNotExist, User.DoesNotExist) as exc:
            raise ValidationError(
                "The post or one or more mentioned users do not exist."
            ) from exc
