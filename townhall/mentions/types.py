from dataclasses import dataclass


@dataclass
class CreateMentionData:
    post_id: int
    mentioned_user_ids: list[int]
