from .types import CreateMentionData

from .models import Mention


class MentionDao:
    @staticmethod
    def create_mentions(data: CreateMentionData):
        mentions = [
            Mention(post_id=data.post_id, mentioned_user_id=user_id)
            for user_id in data.mentioned_user_ids
        ]

        Mention.objects.bulk_create(mentions, ignore_conflicts=True)
