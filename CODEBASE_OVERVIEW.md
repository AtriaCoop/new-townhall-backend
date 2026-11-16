# Townhall Backend — Codebase Overview

> Backend for the Atria Coop "Townhall" community platform.
> Repo: https://github.com/AtriaCoop/new-townhall-backend

## What This Project Does

Townhall is a social/community backend for Atria Coop members. It powers:

- User accounts & professional profiles (orgs, skills, social links, tags)
- A feed of posts with comments, likes, reactions, images, tags, pinning, anonymity
- Direct & group chat (REST + WebSockets)
- Events (create, update, enroll/unenroll)
- In-app notifications (reactions, comments, likes, events)
- Activity history (audit-style feed from `django-simple-history`)
- Admin panel (Jazzmin), email (SendGrid), media (Cloudinary)

Deployed backends/frontends include Render and Netlify (`atriacoop.netlify.app`, `townhallbackend.onrender.com`).

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | Django 5.2 + Django REST Framework |
| Real-time | Django Channels + Daphne (ASGI) |
| Auth | Session auth + CSRF cookies |
| DB | SQLite (local) / Postgres via `DATABASE_URL` (prod) |
| Cache / WS | Redis (prod Channels); InMemoryChannelLayer in DEBUG |
| Media | Cloudinary |
| Email | SendGrid |
| History | django-simple-history |
| Admin UI | django-jazzmin |
| Containers | Docker + docker-compose (backend + frontend) |
| CI | GitHub Actions (tests, black, flake8) + pre-commit |

## Repository Layout

```
new-townhall-backend/
├── README.md                 # Setup & local run guide
├── .github/workflows/        # CI: tests, black, flake8
├── .pre-commit-config.yaml
└── townhall/                 # Django project root (run manage.py here)
    ├── manage.py
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── fixtures/             # Seed JSON fixtures
    ├── townhall/             # Project settings, URLs, ASGI/WSGI, WS routing
    ├── users/                # Auth, profiles, tags, reports
    ├── posts/                # Feed, comments, reactions, images
    ├── chats/                # DMs, groups, messages, WS consumers
    ├── events/               # Calendar-style events
    ├── notifications/        # Bell notifications
    ├── activities/           # User activity timeline (from history)
    └── core/                 # Shared utilities (e.g. cache facade)
```

## Architecture Pattern

Each feature app follows a layered design:

```
HTTP/WS request
    → views.py          (ViewSets / auth endpoints — thin)
        → services.py   (business logic, validation)
            → daos.py   (DB access)
                → models.py
    → serializers.py    (request/response shaping)
    → types.py          (dataclasses / DTOs where used)
```

- **Views**: HTTP adapters; session/permission checks; call services.
- **Services**: Domain rules (create post, toggle reaction, enroll in event, etc.).
- **DAOs**: Querysets / persistence helpers.
- **Models**: Django ORM; many use `HistoricalRecords` for audit trails.
- **Core cache**: `core/cache/CacheFacade` reads/writes list queries via Django cache.

WebSockets (`chats/consumers.py`) broadcast chat/group/user events; persistence is mainly via REST.

## Django Apps (Features)

### 1. `users`
Custom email-based user (`AUTH_USER_MODEL = users.User`).

**Models:** `User`, `Tag`, `Report`

**Capabilities:**
- Signup, login/logout, CSRF, session check
- Email verification, forgot/reset password, change password
- Profile CRUD, complete profile, mention search
- Tags (list, by prefix, per user)
- Privacy: `show_email`, `show_in_directory`, `allow_dms`, `receive_emails`
- Account lockout after failed logins; deactivate/reactivate
- Export user data (JSON/CSV-style streaming)
- User reports

**Key routes:** `/auth/*`, `/user/`, `/user/<id>/`, `/tags/`, `/user/report/`

### 2. `posts`
Community feed.

**Models:** `Post`, `PostImage`, `Comment`, `ReportedPost`, `Reaction`

**Capabilities:**
- CRUD posts; multiple Cloudinary images
- Likes; rich reaction types (love, applaud, fire, etc.)
- Comments (optional anonymous)
- Tags + trending tags
- Pin posts; anonymous author masking
- Report posts; basic profanity filtering (`posts/profanity.py`)

**Key routes:** `/post/`, `/post/<id>/`, `/post/<id>/like/`, `/post/<id>/reaction/`, `/comment/`, `/post/tags/trending/`

### 3. `chats`
Messaging over REST + Channels.

**Models:** `Chat`, `Message`, `MessageReaction`, `ChatReadStatus`, `GroupMessage`

**Capabilities:**
- Direct & group chats (`is_group`)
- Messages with optional images; sent/delivered/read status
- Unread counts; mark chat read; hide chats
- Message reactions
- Named group message channels

**WebSockets** (`townhall/routing.py`):
- `ws/chats/<chat_id>/` — chat room broadcast
- `ws/groups/<group_name>/` — group channel
- `ws/users/<user_id>/` — per-user events (e.g. DM/notification push)

**Key routes:** `/chats/`, `/chats/<id>/messages/`, `/chats/send/`, `/chats/unread-counts/`, `/groups/...`

### 4. `events`
**Model:** `Event` (title, description, date, time string, location, admin, participants)

**Capabilities:** CRUD + participate / unenroll

**Key routes:** `/event/`, `/event/<id>/`, `/event/<id>/participate/`, `/event/<id>/unenroll/`

### 5. `notifications`
**Model:** `Notification` (recipient, actor, type, target_id, detail, is_read)

**Types:** reaction, comment, like, new_event, event_update, event_cancel, event_reminder

**Key routes:** `/notifications/`, unread count, mark read / mark all read

### 6. `activities`
No own model. Aggregates `django-simple-history` records into a human-readable activity feed (“created a post…”, profile updates, etc.).

**Key route:** `/activities/`

### 7. `core`
Shared helpers — e.g. Redis/Django-cache list caching (`CacheFacade` + `key_builder`).

## Auth & Security Notes

- Session cookies + CSRF; CORS allows local frontend and deployed frontends with credentials
- Secure cookies / SameSite when `DEBUG=False`
- Signup throttled (`3/min`); django-ratelimit available
- Password validators, HSTS (prod), XSS/content-type/frame headers
- Upload size capped at ~5MB

## Runtime & Ops

**Local (from `townhall/`):**
```bash
python manage.py migrate
python manage.py runserver          # HTTP only
# For WebSockets:
daphne -p 8000 townhall.asgi:application
redis-server                        # needed for Channels outside DEBUG
```

**Docker:** compose builds backend (Daphne on 8000) and optional frontend from sibling `townhallfrontend`.

**Env (typical):** `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, Cloudinary keys, `SENDGRID_API_KEY`, `FRONTEND_URL`, `REDIS_URL`

## Testing & Quality

- App tests under `*/tests/`
- `python manage.py test` (CI on PRs)
- Black + Flake8 workflows; pre-commit hooks

## Mental Model

Townhall is the API + realtime layer for a co-op member network: directory/profiles, moderated social feed, DMs/groups, events, and notifications — structured as Django apps with a consistent views → services → DAOs stack.
