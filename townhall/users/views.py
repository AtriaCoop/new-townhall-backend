from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from django.forms import ValidationError
from django.contrib.auth import login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from django.middleware.csrf import get_token
import json

from .models import User
from .types import CreateUserData, UpdateUserData, FilterUserData
from .serializers import (
    UserSerializer,
    CreateUserSerializer,
    UserProfileSerializer,
    UpdateUserSerializer,
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
    def create_user(self, request):
        serializer = CreateUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        create_user_data = CreateUserData(
            email=validated_data.get("email"), password=validated_data["password"]
        )

        try:
            user = UserServices.create_user(create_user_data)

            response_serializer = UserSerializer(user)

            return Response(
                {
                    "message": "User Created Successfully",
                    "user": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {
                    "message": "Internal server error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # COMPLETE USER INFORMATION (SETUP)
    @action(detail=True, methods=["post"], url_path="complete_profile")
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
            profile_image=validated_data.get("profile_image"),
            profile_header=validated_data.get("profile_header"),
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
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"message": f"User with id {uid} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception:
            return Response(
                {"message": "Internal server error while updating user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
