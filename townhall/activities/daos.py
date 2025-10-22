from posts.models import Post, Comment, ReportedPost
from users.models import User
from typing import List, Any


class ActivityDao:
    @staticmethod
    def get_user_activities(user_id: int) -> List[Any]:
        post_history = Post.history.filter(user_id=user_id)
        comment_history = Comment.history.filter(user_id=user_id)
        reported_post_history = ReportedPost.history.filter(user_id=user_id)
        user_history = User.history.filter(id=user_id)

        # Sort all activities based on history_date
        all_activities = sorted(
            list(post_history)
            + list(comment_history)
            + list(reported_post_history)
            + list(user_history),
            key=lambda h: h.history_date,
            reverse=True,
        )

        return all_activities
