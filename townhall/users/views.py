from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.forms import ValidationError
from django.contrib.auth import login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from django.middleware.csrf import get_token
import json

from .models import User, Tag
from .types import CreateUserData, UpdateUserData, FilterUserData
from .serializers import (
    UserSerializer,
    CreateUserSerializer,
    UserProfileSerializer,
    UpdateUserSerializer,
    TagSerializer,
)
from .services import UserServices


@ensure_csrf_cookie
def get_csrf_token(request):
    token = get_token(request)
    return JsonResponse({"detail": "CSRF cookie set", "csrfToken": token})


# USER LOGIN
def login_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            # Check if the user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({"error": "User not found"}, status=404)

            # Validate Password
            if check_password(password, user.password):
                login(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )

                return JsonResponse(
                    {
                        "message": "Login successful",
                        "user": {
                            "id": user.id,
                            "full_name": user.full_name,
                            "email": user.email,
                        },
                    },
                    status=200,
                )
            else:
                return JsonResponse({"error": "Invalid password"}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# USER LOGOUT
@csrf_exempt
def logout_user(request):
    if request.method == "POST":
        logout(request)
        response = JsonResponse({"message": "Logged out successfully."})
        response.delete_cookie("sessionid")
        response.delete_cookie("csrftoken")
        return response

    return JsonResponse({"error": "Invalid request method."}, status=405)


class UserViewSet(viewsets.ModelViewSet):

    # CREATE USER
    @action(detail=False, methods=["post"], url_path="user")
    @permission_classes([AllowAny])
    def create_user(self, request):
        print("➡️ Received request to create user")
        print("📨 Request data:", request.data)

        serializer = CreateUserSerializer(data=request.data)

        if not serializer.is_valid():
            print("❌ Serializer invalid:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        print("✅ Serializer validated data:", validated_data)

        create_user_data = CreateUserData(
            email=validated_data.get("email"), password=validated_data["password"]
        )

        try:
            print("🔧 Calling UserServices.create_user")
            user = UserServices.create_user(create_user_data)
            print("✅ User created successfully:", user)

            response_serializer = UserSerializer(user)
            print("📦 Serialized user:", response_serializer.data)

            return Response(
                {
                    "message": "User Created Successfully",
                    "user": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            print("❌ ValidationError while creating user:", str(e))
            return Response(
                {
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            print("🔥 Unexpected error while creating user:", str(e))
            return Response(
                {
                    "message": "Internal server error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # COMPLETE USER INFORMATION (SETUP)
    @action(detail=True, methods=["post"], url_path="complete_profile")
    @permission_classes([IsAuthenticated])
    def complete_profile(self, request, pk=None):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserProfileSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        return Response(
            {"message": "Profile setup completed."}, status=status.HTTP_201_CREATED
        )

    # GET a User
    @action(detail=True, methods=["get"], url_path="user")
    @permission_classes([IsAuthenticated])
    def get_user(self, request, user_id):
        uid = user_id

        try:
            user = UserServices.get_user(uid)

            response_serializer = UserSerializer(user)

            return Response(
                {
                    "message": "User Retreived Successfully",
                    "user": response_serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {
                    "message": str(e),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    # GET ALL USERS
    @action(detail=False, methods=["get"], url_path="user")
    @permission_classes([IsAuthenticated])
    def get_user_all(self, request):

        serializer = UpdateUserSerializer(data=request.query_params)

        users = None
        message = None
        if serializer.is_valid():
            validated_data = serializer.validated_data

            filter_user_data = FilterUserData(
                full_name=validated_data.get("full_name", None),
                email=validated_data.get("email", None),
            )

            users = UserServices.get_user_all(filter_user_data)
            message = "All users with the given filters retreived successfully"

        else:
            users = UserServices.get_user_all(None)
            message = "All Users retreived successfully"

        if not users:
            return Response(
                {"message": "No Users were found"},
                status=status.HTTP_200_OK,
            )

        response_serializer = UserSerializer(users, many=True)
        return Response(
            {
                "message": message,
                "data": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # DELETE A USER
    @action(detail=True, methods=["delete"], url_path="user")
    def delete_user(self, request, user_id):
        uid = user_id

        # Check if user is trying to delete their own profile
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if int(user_id) != uid:
            return Response(
                {"error": "You can only delete your own profile"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            UserServices.delete_user(uid)

            return Response(
                {"message": "User Delete Successfully"},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)

    # UPDATE A USER BY ID
    @action(detail=True, methods=["patch"], url_path="user")
    def update_user(self, request, user_id):
        uid = user_id

        # Check if user is trying to update their own profile
        user_id = request.session.get("_auth_user_id")
        if not user_id:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if int(user_id) != uid:
            return Response(
                {"error": "You can only update your own profile"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UpdateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        update_user_data = UpdateUserData(
            id=uid,
            full_name=validated_data.get("full_name"),
            email=validated_data.get("email"),
            pronouns=validated_data.get("pronouns"),
            title=validated_data.get("title"),
            primary_organization=validated_data.get("primary_organization"),
            other_organizations=validated_data.get("other_organizations"),
            other_networks=validated_data.get("other_networks"),
            about_me=validated_data.get("about_me"),
            skills_interests=validated_data.get("skills_interests"),
            profile_image=request.FILES.get("profile_image"),
            receive_emails=validated_data.get("receive_emails"),
            tags=validated_data.get("tags", []),
            linkedin_url=validated_data.get("linkedin_url"),
            facebook_url=validated_data.get("facebook_url"),
            x_url=validated_data.get("x_url"),
            instagram_url=validated_data.get("instagram_url"),
        )
        try:
            UserServices.update_user(update_user_data)

            return Response(
                {
                    "message": "User Updated Successfully",
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            # Extract the actual error message from ValidationError
            if hasattr(e, "messages") and e.messages:
                error_message = e.messages[0]
            elif hasattr(e, "message"):
                error_message = e.message
            else:
                # Fallback: clean up string representation
                error_message = str(e).strip("[]'\"")

            return Response(
                {"message": error_message}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Print the error for debugging
            print(f"Unexpected error in update_user: {e}")
            print(f"Error type: {type(e).__name__}")

    # SEARCH USERS TO MENTION
    @action(detail=False, methods=["get"], url_path="mention")
    @permission_classes([IsAuthenticated])
    def mention_user(self, request):

        query = request.query_params.get("query", "")

        try:
            results = UserServices.search_users_for_mention(query)
            serialized_results = UserSerializer(results, many=True).data

            return Response(
                {
                    "message": "Here are your search results",
                    "search_results": serialized_results,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    @action(detail=False, methods=["get"], url_path="given-prefix")
    def get_tags_given_prefix(self, request):
        prefix = request.query_params.get("prefix", "")

        tags = Tag.objects.filter(name__istartswith=prefix).order_by("name")
        serialized = self.get_serializer(tags, many=True).data

        return Response(serialized, status=status.HTTP_200_OK)
    permission_classes = [AllowAny]

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="user/tags",
    )
    def get_all_tags_for_a_user(self, request):
        """Return Tag objects for the current user or for the user_id query param."""
        # Prefer request.GET for explicitness in tests; handle empty string too.
        user_id_param = request.GET.get("user_id", None)

        if user_id_param is not None:
            # treat empty string as invalid
            if user_id_param == "":
                return Response(
                    {"detail": "Invalid user_id"}, status=status.HTTP_400_BAD_REQUEST
                )
            try:
                user_id = int(user_id_param)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "Invalid user_id"}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            if not getattr(request, "user", None) or not request.user.is_authenticated:
                return Response(
                    {"detail": "Authentication credentials were not provided."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            user_id = request.user.id

        tags_qs = UserServices.get_tags_for_user(user_id)
        serializer = self.get_serializer(tags_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def get_all_tags(self, request):
        """Get all available tags"""
        tags = UserServices.get_all_tags()
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)
