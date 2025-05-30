from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from django.forms import ValidationError
from django.utils import timezone

from .models import User, Post, Comment
from .types import CreatePostData, UpdatePostData, CreateCommentData
from .serializers import PostSerializer, CreateCommentSerializer, CommentSerializer
from .services import PostServices, CommentServices


class PostViewSet(viewsets.ModelViewSet):

    # GET A POST
    @action(detail=True, methods=["get"], url_path="post")
    def get_post(self, request, pk=None):
        try:
            post = PostServices.get_post(id=pk)
            serializer = PostSerializer(post)
            return Response({
                "message": "Post fetched successfully",
                "post": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    # GET ALL POSTS
    @action(detail=False, methods=["get"], url_path="post")
    def get_post_all(self, request):
        try:
            posts = PostServices.get_all_posts()
            serializer = PostSerializer(posts, many=True)
            return Response({
                "message": "Posts fetched successfully",
                "posts": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # CREATE POST
    @action(detail=False, methods=["post"], url_path="post")
    def create_post(self, request):
        serializer = PostSerializer(data=request.data)

        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        create_post_data = CreatePostData(
            user_id=validated_data["user"].id,
            content=validated_data["content"],
            created_at=timezone.now(),
            image=validated_data.get("image", None),
        )

        try:
            post = PostServices.create_post(create_post_data)
            response_serializer = PostSerializer(post)
            return Response(
                {
                    "message": "Post Created Successfully",
                    "post": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # UPDATE POST
    @action(detail=True, methods=["patch"], url_path="post")
    def update_post(self, request, pk=None):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PostSerializer(post, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        update_post_data = UpdatePostData(
            content=serializer.validated_data.get("content", ""),
            image=serializer.validated_data.get("image", None),
        )

        from .services import PostServices as PostServices
        PostServices.update_post(pk, update_post_data)

        return Response(
            {"message": "Post Updated Successfully"},
            status=status.HTTP_200_OK
        )

    # DELETE A POST
    @action(detail=True, methods=["delete"], url_path="post")
    def delete_post(self, request, pk=None):
        try:
            PostServices.delete_post(post_id=pk)
            return Response(
                {"message": "Post deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    # LIKE A POST
    @action(detail=True, methods=["patch"], url_path="like")
    def like_post(self, request, pk=None):
        try:
            post = Post.objects.get(pk=pk)

            # Here: fetch user ID from session
            user_id = request.session.get("_auth_user_id")
            if not user_id:
                return Response(
                    {"error": "Not authenticated"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user in post.liked_by.all():
                post.liked_by.remove(user)
                post.likes -= 1
                post.save()
                return Response(
                    {
                        "message": "Post unliked",
                        "likes": post.likes
                    },
                    status=status.HTTP_200_OK
                )
            else:
                post.liked_by.add(user)
                post.likes += 1
                post.save()
                return Response(
                    {
                        "message": "Post liked",
                        "likes": post.likes
                    },
                    status=status.HTTP_200_OK
                )

        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class CommentViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Comment.objects.all()

    # CREATE A COMMENT
    @action(detail=False, methods=["post"], url_path="comment")
    def create_comment(self, request):
        # Transforms requests JSON data into a python dictionary
        serializer = CreateCommentSerializer(data=request.data)

        # If the data is NOT valid return with a message serializers errors
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        create_comment_data = CreateCommentData(
            user_id=validated_data["user"].id,
            post_id=validated_data["post"].id,
            content=validated_data["content"],
            created_at=validated_data["created_at"],
        )

        try:
            comment = CommentServices.create_comment(create_comment_data)

            response_serializer = CommentSerializer(comment)

            return Response(
                {
                    "message": "Comment Created Succesfully",
                    "comment": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # DELETE COMMENT (only by author)
    def destroy(self, request, *args, **kwargs):
        try:
            comment = self.get_object()
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get current user from session
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Allow only the author to delete
        if comment.user.id != int(user_id):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Authorized – delete it
        comment.delete()
        return Response(
            {"message": "Comment deleted"},
            status=status.HTTP_204_NO_CONTENT
        )
