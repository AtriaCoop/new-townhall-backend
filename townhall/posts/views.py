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
from .types import CreatePostData, UpdatePostData, CreateCommentData, ReportedPostData
from .serializers import (
    PostSerializer,
    CreateCommentSerializer,
    CommentSerializer,
    ReportedPostSerializer,
)
from .services import PostServices, CommentServices, ReportedPostServices


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
            posts, total_pages = PostServices.get_all_posts()
            serializer = PostSerializer(posts, many=True)
            return Response(
                {"message": "Posts fetched successfully", "posts": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # CREATE POST
    @action(detail=False, methods=["post"], url_path="post")
    def create_post(self, request):
        # Check if user is authenticated
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PostSerializer(data=request.data)

        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.is_authenticated:
            return Response(
                {"message": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )
        validated_data = serializer.validated_data

        create_post_data = CreatePostData(
            user_id=user.id,
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
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is trying to update their own post
        if int(user_id) != post.user.id:
            return Response(
                {"error": "You can only update your own posts"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PostSerializer(post, data=request.data, partial=True)
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"message": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )
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
        # Check if user is authenticated
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if user is trying to delete their own post
        if int(user_id) != post.user.id:
            return Response(
                {"error": "You can only delete your own posts"},
                status=status.HTTP_403_FORBIDDEN
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
        try:
            post = Post.objects.get(pk=pk)

            # Here: fetch user ID from session
            user_id = request.session.get("_auth_user_id")
            if not user_id:
                return Response(
                    {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
                )

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST
                )

            if user in post.liked_by.all():
                post.liked_by.remove(user)
                post.likes -= 1
                post.save()
                return Response(
                    {"message": "Post unliked", "likes": post.likes},
                    status=status.HTTP_200_OK,
                )
            else:
                post.liked_by.add(user)
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
        # Check if user is authenticated
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST
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
            user_id=user.id,
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


class CommentViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Comment.objects.all()

    # CREATE A COMMENT
    @action(detail=False, methods=["post"], url_path="comment")
    def create_comment(self, request):
        # Check if user is authenticated
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Transforms requests JSON data into a python dictionary
        serializer = CreateCommentSerializer(data=request.data)

        # If the data is NOT valid return with a message serializers errors
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        create_comment_data = CreateCommentData(
            user_id=user.id,
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
        # Check if user is authenticated
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            comment = self.get_object()
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Allow only the author to delete
        if comment.user.id != int(user_id):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Authorized – delete it
        comment.delete()
        return Response(
            {"message": "Comment deleted"}, status=status.HTTP_204_NO_CONTENT
        )
