from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.forms import ValidationError
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth.hashers import check_password
from django.middleware.csrf import get_token
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from rest_framework.throttling import AnonRateThrottle
from datetime import timedelta
import csv
import json
from .models import User, Tag
from .types import (
    CreateUserData,
    UpdateUserData,
    FilterUserData,
    CreateReportData,
)
from .serializers import (
    UserSerializer,
    CreateUserSerializer,
    UserProfileSerializer,
    UpdateUserSerializer,
    TagSerializer,
    ReportSerializer,
)
from .services import UserServices, ReportServices
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class SignupThrottle(AnonRateThrottle):
    rate = "3/min"


def _send_verification_email(user):
    """Send an email verification link to the given user via SendGrid."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    verify_url = f"{settings.FRONTEND_URL}/VerifyEmailPage" f"?uid={uid}&token={token}"

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=user.email,
        subject="Townhall - Verify Your Email",
        plain_text_content=(
            f"Hi there,\n\n"
            f"Thanks for signing up! Please verify your email by clicking "
            f"the link below:\n"
            f"{verify_url}\n\n"
            f"This link expires in 1 hour.\n\n"
            f"If you didn't create this account, you can ignore this email."
        ),
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(message)


@ensure_csrf_cookie
def get_csrf_token(request):
    token = get_token(request)
    return JsonResponse({"detail": "CSRF cookie set", "csrfToken": token})


def check_session(request):
    if request.user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": True,
                "user": {
                    "id": request.user.id,
                    "full_name": request.user.full_name,
                    "email": request.user.email,
                    "email_verified": request.user.email_verified,
                },
            }
        )
    return JsonResponse({"authenticated": False}, status=401)


class Echo:
    def write(self, value):
        return value


def _format_datetime(value):
    return value.isoformat() if value else None


def _cloudinary_url(value):
    return value.url if value else None


def export_user_data(request):
    # Exporting data is read-only, so only GET should be allowed.
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    # Logged-out users should not be able to export anything.
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    from chats.models import GroupMessage, Message
    from posts.models import Comment, Post

    # Default to JSON if the frontend does not provide a format.
    export_format = request.GET.get("format", "json").lower()
    user = request.user

    if export_format not in {"json", "csv"}:
        return JsonResponse(
            {"error": "format must be either 'json' or 'csv'"},
            status=400,
        )

    # Export as CSV.
    if export_format == "csv":
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        def stream_rows():
            """
            Generator that yields CSV rows for the authenticated user's exported data.

            Yields the header row first, followed by rows for posts, comments,
            direct messages, and group messages — in that order. Each row is a
            formatted string produced by csv.writer, ready to be streamed via
            StreamingHttpResponse.

            Yields:
                str: A single CSV-formatted row.
            """
            yield writer.writerow(
                [
                    "type",
                    "id",
                    "content",
                    "created_at",
                    "post_id",
                    "chat_id",
                    "group_name",
                    "image_url",
                ]
            )

            for post in (
                Post.objects.filter(user=user)
                .order_by("created_at", "id")
                .values("id", "content", "created_at")
                .iterator()
            ):
                yield writer.writerow(
                    [
                        "post",
                        post["id"],
                        post["content"],
                        _format_datetime(post["created_at"]),
                        "",
                        "",
                        "",
                        "",
                    ]
                )

            for comment in (
                Comment.objects.filter(user=user)
                .order_by("created_at", "id")
                .values("id", "content", "created_at", "post_id")
                .iterator()
            ):
                yield writer.writerow(
                    [
                        "comment",
                        comment["id"],
                        comment["content"],
                        _format_datetime(comment["created_at"]),
                        comment["post_id"],
                        "",
                        "",
                        "",
                    ]
                )

            for message in (
                Message.objects.filter(user=user)
                .order_by("sent_at", "id")
                .only("id", "content", "sent_at", "chat_id", "image_content")
                .iterator()
            ):
                image_url = _cloudinary_url(message.image_content)
                yield writer.writerow(
                    [
                        "direct_message",
                        message.id,
                        message.content,
                        _format_datetime(message.sent_at),
                        "",
                        message.chat_id,
                        "",
                        image_url or "",
                    ]
                )

            for group_message in (
                GroupMessage.objects.filter(user=user)
                .order_by("sent_at", "id")
                .only("id", "content", "sent_at", "group_name", "image")
                .iterator()
            ):
                image_url = _cloudinary_url(group_message.image)
                yield writer.writerow(
                    [
                        "group_message",
                        group_message.id,
                        group_message.content,
                        _format_datetime(group_message.sent_at),
                        "",
                        "",
                        group_message.group_name,
                        image_url or "",
                    ]
                )

        response = StreamingHttpResponse(stream_rows(), content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="townhall-user-data.csv"'
        )
        return response

    # Export as JSON.
    posts = [
        {
            "id": post["id"],
            "content": post["content"],
            "created_at": _format_datetime(post["created_at"]),
            "likes": post["likes"],
            "pinned": post["pinned"],
            "anonymous": post["anonymous"],
        }
        for post in Post.objects.filter(user=user)
        .order_by("created_at", "id")
        .values(
            "id",
            "content",
            "created_at",
            "likes",
            "pinned",
            "anonymous",
        )
    ]

    comments = [
        {
            "id": comment["id"],
            "post_id": comment["post_id"],
            "content": comment["content"],
            "created_at": _format_datetime(comment["created_at"]),
            "anonymous": comment["anonymous"],
        }
        for comment in Comment.objects.filter(user=user)
        .order_by("created_at", "id")
        .values(
            "id",
            "post_id",
            "content",
            "created_at",
            "anonymous",
        )
    ]

    direct_messages = [
        {
            "id": message.id,
            "chat_id": message.chat_id,
            "content": message.content,
            "image_url": _cloudinary_url(message.image_content),
            "sent_at": _format_datetime(message.sent_at),
        }
        for message in Message.objects.filter(user=user)
        .order_by("sent_at", "id")
        .only(
            "id",
            "chat_id",
            "content",
            "image_content",
            "sent_at",
        )
    ]

    group_messages = [
        {
            "id": group_message.id,
            "group_name": group_message.group_name,
            "content": group_message.content,
            "image_url": _cloudinary_url(group_message.image),
            "sent_at": _format_datetime(group_message.sent_at),
        }
        for group_message in GroupMessage.objects.filter(user=user)
        .order_by("sent_at", "id")
        .only(
            "id",
            "group_name",
            "content",
            "image",
            "sent_at",
        )
    ]

    response = JsonResponse(
        {
            "exported_at": timezone.now().isoformat(),
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "pronouns": user.pronouns,
                "title": user.title,
                "primary_organization": user.primary_organization,
                "other_organizations": user.other_organizations,
                "other_networks": user.other_networks,
                "about_me": user.about_me,
                "skills_interests": user.skills_interests,
                "profile_image_url": _cloudinary_url(user.profile_image),
                "profile_header_url": _cloudinary_url(user.profile_header),
                "date_joined": _format_datetime(user.date_joined),
                "receive_emails": user.receive_emails,
                "show_email": user.show_email,
                "show_in_directory": user.show_in_directory,
                "allow_dms": user.allow_dms,
                "linkedin_url": user.linkedin_url,
                "facebook_url": user.facebook_url,
                "x_url": user.x_url,
                "instagram_url": user.instagram_url,
                "bluesky_url": user.bluesky_url,
            },
            "posts": posts,
            "comments": comments,
            "direct_messages": direct_messages,
            "group_messages": group_messages,
        },
        json_dumps_params={"indent": 2},
    )
    response["Content-Disposition"] = 'attachment; filename="townhall-user-data.json"'
    return response


# USER LOGIN
@ratelimit(key="ip", rate="5/m", method="POST", block=False)
def login_user(request):
    if request.method == "POST":
        if getattr(request, "limited", False):
            return JsonResponse(
                {"error": "Too many login attempts. Please try again later."},
                status=429,
            )

        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            # Check if the user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse(
                    {"error": "Invalid email or password"},
                    status=401,
                )

            # Check account lockout
            if user.locked_until and timezone.now() < user.locked_until:
                return JsonResponse(
                    {"error": "Account locked. Try again later."},
                    status=429,
                )

            # Validate Password
            if check_password(password, user.password):
                # Block login if account is deactivated
                if not user.is_active:
                    return JsonResponse(
                        {
                            "error": "account_deactivated",
                            "message": (
                                "Your account has been deactivated. "
                                "You can reactivate it to sign in again."
                            ),
                        },
                        status=403,
                    )

                # TODO: Re-enable email verification once a proper
                # sending domain is configured
                # Block login if email is not verified
                # if not user.email_verified:
                #     return JsonResponse(
                #         {
                #             "error": (
                #                 "Please verify your email before signing in. "
                #                 "Check your inbox for a verification link."
                #             ),
                #         },
                #         status=403,
                #     )

                # Reset failed attempts on successful login
                if user.failed_login_attempts > 0:
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    user.save(
                        update_fields=[
                            "failed_login_attempts",
                            "locked_until",
                        ]
                    )

                login(
                    request,
                    user,
                    backend="django.contrib.auth.backends.ModelBackend",
                )

                return JsonResponse(
                    {
                        "message": "Login successful",
                        "user": {
                            "id": user.id,
                            "full_name": user.full_name,
                            "email": user.email,
                            "email_verified": user.email_verified,
                        },
                    },
                    status=200,
                )
            else:
                # Increment failed attempts and lock after 5 failures
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = timezone.now() + timedelta(minutes=15)
                user.save(update_fields=["failed_login_attempts", "locked_until"])
                return JsonResponse(
                    {"error": "Invalid email or password"},
                    status=401,
                )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# USER LOGOUT
def logout_user(request):
    if request.method == "POST":
        logout(request)
        response = JsonResponse({"message": "Logged out successfully."})
        response.delete_cookie("sessionid")
        response.delete_cookie("csrftoken")
        return response

    return JsonResponse({"error": "Invalid request method."}, status=405)


# CHANGE PASSWORD
def change_password(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=401)

        try:
            data = json.loads(request.body)
            current_password = data.get("current_password")
            new_password = data.get("new_password")

            if not current_password or not new_password:
                return JsonResponse(
                    {"error": "current_password and new_password required"},
                    status=400,
                )

            if not check_password(current_password, request.user.password):
                return JsonResponse(
                    {"error": "Current password is incorrect"},
                    status=400,
                )

            try:
                validate_password(new_password, request.user)
            except DjangoValidationError as e:
                return JsonResponse({"error": e.messages[0]}, status=400)

            request.user.set_password(new_password)
            request.user.save()

            # Re-authenticate to refresh session hash after password change
            login(
                request,
                request.user,
                backend="django.contrib.auth.backends.ModelBackend",
            )

            return JsonResponse({"message": "Password changed successfully"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# FORGOT PASSWORD - Send Reset Email
@ratelimit(key="ip", rate="3/m", method="POST", block=False)
def forgot_password(request):
    if request.method == "POST":
        if getattr(request, "limited", False):
            return JsonResponse(
                {"error": "Too many requests. Please try again later."},
                status=429,
            )
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)

            # Always return success to prevent email enumeration
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                reset_url = (
                    f"{settings.FRONTEND_URL}/ResetPasswordPage"
                    f"?uid={uid}&token={token}"
                )

                # ✅ Send email using SendGrid API
                message = Mail(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=user.email,
                    subject="Townhall - Reset Your Password",
                    plain_text_content=(
                        f"Hi {user.full_name or 'there'},\n\n"
                        f"Click the link below to reset your password:\n"
                        f"{reset_url}\n\n"
                        f"This link expires in 1 hour.\n\n"
                        f"If you didn't request this, ignore this email."
                    ),
                )

                sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
                sg.send(message)

            except User.DoesNotExist:
                pass  # Don't reveal whether email exists

            return JsonResponse(
                {
                    "message": (
                        "If an account exists with that email, "
                        "a reset link has been sent."
                    ),
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# RESET PASSWORD - Validate Token and Set New Password
@ratelimit(key="ip", rate="5/m", method="POST", block=False)
def reset_password(request):
    if request.method == "POST":
        if getattr(request, "limited", False):
            return JsonResponse(
                {"error": "Too many requests. Please try again later."},
                status=429,
            )

        try:
            data = json.loads(request.body)
            uid = data.get("uid")
            token = data.get("token")
            new_password = data.get("new_password")

            if not uid or not token or not new_password:
                return JsonResponse(
                    {"error": "uid, token, and new_password are required"},
                    status=400,
                )

            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return JsonResponse({"error": "Invalid reset link"}, status=400)

            if not default_token_generator.check_token(user, token):
                return JsonResponse(
                    {"error": "Reset link has expired or is invalid"},
                    status=400,
                )

            try:
                validate_password(new_password, user)
            except DjangoValidationError as e:
                return JsonResponse({"error": e.messages[0]}, status=400)

            user.set_password(new_password)
            user.save()

            return JsonResponse({"message": "Password has been reset successfully"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# VERIFY EMAIL - Validate Token and Mark Verified
@ratelimit(key="ip", rate="10/m", method="POST", block=False)
def verify_email(request):
    if request.method == "POST":
        if getattr(request, "limited", False):
            return JsonResponse(
                {"error": "Too many requests. Please try again later."},
                status=429,
            )

        try:
            data = json.loads(request.body)
            uid = data.get("uid")
            token = data.get("token")

            if not uid or not token:
                return JsonResponse(
                    {"error": "uid and token are required"},
                    status=400,
                )

            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return JsonResponse(
                    {"error": "Invalid verification link"},
                    status=400,
                )

            if not default_token_generator.check_token(user, token):
                return JsonResponse(
                    {"error": "Verification link has expired or is invalid"},
                    status=400,
                )

            user.email_verified = True
            user.save(update_fields=["email_verified"])

            return JsonResponse(
                {"message": "Email verified successfully. You can now sign in."}
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# RESEND VERIFICATION EMAIL
@ratelimit(key="ip", rate="3/m", method="POST", block=False)
def resend_verification(request):
    if request.method == "POST":
        if getattr(request, "limited", False):
            return JsonResponse(
                {"error": "Too many requests. Please try again later."},
                status=429,
            )

        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)

            # Always return success to prevent email enumeration
            try:
                user = User.objects.get(email=email)
                if not user.email_verified:
                    _send_verification_email(user)
            except User.DoesNotExist:
                pass

            return JsonResponse(
                {
                    "message": (
                        "If an account exists with that email, "
                        "a new verification link has been sent."
                    ),
                }
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# DEACTIVATE ACCOUNT
def deactivate_account(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=401)

        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])

        logout(request)
        response = JsonResponse({"message": "Account deactivated successfully."})
        response.delete_cookie("sessionid")
        response.delete_cookie("csrftoken")
        return response

    return JsonResponse({"error": "Invalid request method"}, status=405)


# REACTIVATE ACCOUNT
def reactivate_account(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return JsonResponse(
                    {"error": "Email and password are required"},
                    status=400,
                )

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse(
                    {"error": "Invalid email or password"},
                    status=401,
                )

            if not check_password(password, user.password):
                return JsonResponse(
                    {"error": "Invalid email or password"},
                    status=401,
                )

            if user.is_active:
                return JsonResponse(
                    {"message": "Account is already active."},
                    status=200,
                )

            user.is_active = True
            user.save(update_fields=["is_active"])

            return JsonResponse(
                {"message": "Account reactivated successfully. You can now sign in."}
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


class UserViewSet(viewsets.ModelViewSet):

    # CREATE USER
    @action(
        detail=False,
        methods=["post"],
        url_path="user",
        throttle_classes=[SignupThrottle],
    )
    @permission_classes([AllowAny])
    def create_user(self, request):
        serializer = CreateUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        create_user_data = CreateUserData(
            email=validated_data.get("email"),
            password=validated_data["password"],
        )

        try:
            user = UserServices.create_user(create_user_data)

            # TODO: Re-enable once a proper sending domain is configured
            # try:
            #     _send_verification_email(user)
            # except Exception:
            #     pass

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
                {"message": "Internal server error"},
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
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserProfileSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        return Response(
            {"message": "Profile setup completed."},
            status=status.HTTP_201_CREATED,
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

        # Filter out deactivated users and users who opted out of directory
        if users is not None:
            users = users.filter(is_active=True, show_in_directory=True)

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
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if request.user.id != user_id:
            return Response(
                {"error": "You can only delete your own profile"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            UserServices.delete_user(user_id)
            logout(request)

            return Response(
                {"message": "User Delete Successfully"},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

    # UPDATE A USER BY ID
    @action(detail=True, methods=["patch"], url_path="user")
    def update_user(self, request, user_id):
        uid = user_id

        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if request.user.id != uid:
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
            profile_header=request.FILES.get("profile_header"),
            remove_profile_header=validated_data.get("remove_profile_header"),
            receive_emails=validated_data.get("receive_emails"),
            show_email=validated_data.get("show_email"),
            show_in_directory=validated_data.get("show_in_directory"),
            allow_dms=validated_data.get("allow_dms"),
            tags=validated_data.get("tags", []),
            linkedin_url=validated_data.get("linkedin_url"),
            facebook_url=validated_data.get("facebook_url"),
            x_url=validated_data.get("x_url"),
            instagram_url=validated_data.get("instagram_url"),
            bluesky_url=validated_data.get("bluesky_url"),
            is_verified=validated_data.get("is_verified"),
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
        except Exception:
            return Response(
                {"message": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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

    def list(self, request):
        """List users with optional filters: full_name, email, tags."""
        tags = request.query_params.getlist("tags")
        full_name = request.query_params.get("full_name")
        email = request.query_params.get("email")

        filter_user_data = FilterUserData(
            full_name=full_name,
            email=email,
            tags=tags if tags else None,
        )

        users = UserServices.get_user_all(filter_user_data)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        """Return Tag objects for current user or user_id query param."""
        # Prefer request.GET for explicitness in tests; handle empty string too.
        user_id_param = request.GET.get("user_id", None)

        if user_id_param is not None:
            # treat empty string as invalid
            if user_id_param == "":
                return Response(
                    {"detail": "Invalid user_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                user_id = int(user_id_param)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "Invalid user_id"},
                    status=status.HTTP_400_BAD_REQUEST,
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


class ReportViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=["post"], url_path="report")
    def create_report_request(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = ReportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        create_report_data = CreateReportData(
            user_id=request.user.id,
            content=validated_data["content"],
            created_at=timezone.now(),
        )

        try:
            report = ReportServices.create_report(create_report_data)
            response_serializer = ReportSerializer(report)
            return Response(
                {
                    "message": "Report Created Successfully",
                    "success": True,
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )

    # get a report
    @action(detail=True, methods=["get"], url_path="report_id")
    @permission_classes([IsAuthenticated])
    def get_report(self, request, report_id):
        rid = report_id

        try:
            report = ReportServices.get_report(rid)

            response_serializer = ReportSerializer(report)

            return Response(
                {
                    "message": "Report Retrieved Successfully",
                    "success": True,
                    "report": response_serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {
                    "message": str(e),
                    "success": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
