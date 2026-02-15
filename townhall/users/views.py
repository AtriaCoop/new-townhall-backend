from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.forms import ValidationError
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
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


@ensure_csrf_cookie
def get_csrf_token(request):
    token = get_token(request)
    return JsonResponse({"detail": "CSRF cookie set", "csrfToken": token})


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

        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if request.user.id != uid:
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
