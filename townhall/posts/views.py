from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.forms import ValidationError
from django.utils import timezone
from .models import User, Post, Comment
from .types import (
    CreatePostData,
    UpdatePostData,
    CreateCommentData,
    ReportedPostData,
    UpdateCommentData,
)
from .serializers import (
    PostSerializer,
    CreateCommentSerializer,
    CommentSerializer,
    ReportedPostSerializer,
)
from .services import (
    PostServices,
    CommentServices,
    ReportedPostServices,
    ReactionServices,
)
from .types import ToggleReactionData


class PostViewSet(viewsets.ModelViewSet):

    # GET A POST
    @action(detail=True, methods=["get"], url_path="post")
    @permission_classes([AllowAny])
    def get_post(self, request, pk=None):
        try:
            post = PostServices.get_post(id=pk)
            serializer = PostSerializer(post)
            return Response(
                {"message": "Post fetched successfully", "post": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    # GET ALL POSTS
    @action(detail=False, methods=["get"], url_path="post")
    @permission_classes([AllowAny])
    def get_post_all(self, request):
        try:
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))

            posts, total_pages = PostServices.get_all_posts(page, limit)
            serializer = PostSerializer(posts, many=True)
            return Response(
                {
                    "message": "Posts fetched successfully",
                    "posts": serializer.data,
                    "page": page,
                    "limit": limit,
                    "total_pages": total_pages,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # CREATE POST
    @action(detail=False, methods=["post"], url_path="post")
    def create_post(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = PostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        create_post_data = CreatePostData(
            user_id=request.user.id,
            content=validated_data["content"],
            created_at=timezone.now(),
            image=validated_data.get("image", None),
            pinned=validated_data.get("pinned", False),
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
        except PermissionDenied as e:
            return Response({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)

    # UPDATE POST
    @action(detail=True, methods=["patch"], url_path="post")
    def update_post(self, request, pk=None):
        # Check if user is authenticated
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"message": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = PostSerializer(post, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if (
            not post.user_id == user.id
            and serializer.validated_data.get("content")
            or serializer.validated_data.get("image")
        ):
            return Response(
                {"message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        update_post_data = UpdatePostData(
            content=serializer.validated_data.get("content", None),
            image=serializer.validated_data.get("image", None),
            pinned=serializer.validated_data.get("pinned", None),
            user_id=user.id,
        )

        try:
            PostServices.update_post(pk, update_post_data)
            return Response(
                {"message": "Post Updated Successfully"}, status=status.HTTP_200_OK
            )
        except PermissionDenied as e:
            return Response({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)

    # DELETE A POST
    @action(detail=True, methods=["delete"], url_path="post")
    def delete_post(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if request.user.id != post.user.id:
            return Response(
                {"error": "You can only delete your own posts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            PostServices.delete_post(post_id=pk)
            return Response(
                {"message": "Post deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    # LIKE A POST
    @action(detail=True, methods=["patch"], url_path="like")
    def like_post(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            post = Post.objects.get(pk=pk)

            if request.user in post.liked_by.all():
                post.liked_by.remove(request.user)
                post.likes -= 1
                post.save()
                return Response(
                    {"message": "Post unliked", "likes": post.likes},
                    status=status.HTTP_200_OK,
                )
            else:
                post.liked_by.add(request.user)
                post.likes += 1
                post.save()
                return Response(
                    {"message": "Post liked", "likes": post.likes},
                    status=status.HTTP_200_OK,
                )

        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

    # REPORT A POST
    @action(detail=True, methods=["post"], url_path="report")
    def report_post(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReportedPostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        create_reported_post_data = ReportedPostData(
            user_id=request.user.id,
            post_id=post.id,
            created_at=timezone.now(),
        )

        try:
            reported_post = ReportedPostServices.create_reported_post(
                create_reported_post_data=create_reported_post_data
            )
            response_serializer = ReportedPostSerializer(reported_post)
            return Response(
                {
                    "message": "Successfully reported post",
                    "reported_post": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            errorMessage = e.detail[0]
            return Response(
                {"message": errorMessage}, status=status.HTTP_400_BAD_REQUEST
            )

        except IntegrityError as e:
            return Response(
                {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["patch"], url_path="reaction")
    def toggle_reaction(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        reaction_type = request.data.get("reaction_type")
        if not reaction_type:
            return Response(
                {"error": "Reaction type is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reaction_data = ToggleReactionData(
                user_id=request.user.id, post_id=int(pk), reaction_type=reaction_type
            )

            # Delegate business logic to service layer
            was_added, message = ReactionServices.toggle_reaction(reaction_data)

            # Get updated post with reactions
            post = Post.objects.get(pk=pk)
            serializer = PostSerializer(post)

            return Response(
                {"message": message, "reactions": serializer.data["reactions"]},
                status=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except IntegrityError:
            return Response(
                {"error": "Database constraint violation. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as e:
            # Handle invalid integer conversion
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CommentViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Comment.objects.all()

    # CREATE A COMMENT
    @action(detail=False, methods=["post"], url_path="comment")
    def create_comment(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = CreateCommentSerializer(data=request.data)

        # If the data is NOT valid return with a message serializers errors
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        create_comment_data = CreateCommentData(
            user_id=request.user.id,
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

    def update_comment(self, request, pk=None):
        user = request.user
        if not user or not user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            comment = CommentServices.get_comment(pk)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if comment.user != user:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if "content" not in serializer.validated_data:
            return Response(
                {"error": "No updatable fields provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        update_comment_data = UpdateCommentData(
            content=serializer.validated_data["content"],
        )

        try:
            CommentServices.update_comment(pk, update_comment_data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Comment Updated Successfully"}, status=status.HTTP_200_OK
        )

    # DELETE COMMENT (only by author)
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            comment = self.get_object()
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if comment.user.id != request.user.id:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Authorized – delete it
        comment.delete()
        return Response(
            {"message": "Comment deleted"}, status=status.HTTP_204_NO_CONTENT
        )
