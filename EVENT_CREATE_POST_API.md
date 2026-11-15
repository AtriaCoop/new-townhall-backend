# Event posts API

This guide covers creating and updating a community post associated with an
event. The `events` app owns the event and the link to its post; the `posts` app
owns the post content, author, tags, and feed behavior.

An event can have at most one linked post.

## How events and posts are related

The event stores a nullable one-to-one reference to a `Post`:

- Creating an event post creates a regular post through the posts app, then
  links it to the event.
- The post is authored by the event admin and initially gets the `event` tag.
- The event API response exposes whether a post is linked with `hasPost`.
  It does not expose the associated post's ID or content in that event object.
- The event's one-to-one link is nullable and uses `SET_NULL` when a post is
  deleted. Deleting a post therefore leaves the event intact but clears its
  post link; a subsequent create-event-post request can create a new one.

### What happens when an event is deleted

Deleting an event does **not** delete its associated post. Before deleting the
event, the event model changes the linked post's status to `cancelled`; the
post row and its content remain.

Currently, the normal posts query does not filter out cancelled posts, and the
post response serializer does not include the status field. As a result, a
cancelled event post may still appear in the post feed and will not be
identifiable as cancelled from that response alone. Event deletion itself is
available at `DELETE /event/{event_id}/`; it requires authentication and is
allowed to the event admin or a staff user.

## Endpoint

```http
POST /event/{event_id}/create-event-post/
```

The route is mounted at the backend root (there is no `/api/` prefix). For
example:

```text
https://<backend-host>/event/42/create-event-post/
```

The trailing slash is part of the route.

## Authentication and authorization

- The caller must be signed in using the backend's session authentication.
  Include the authenticated session cookie with the request; this endpoint is
  not configured for bearer-token authentication.
- Because this is a `POST` authenticated with a session, include a valid CSRF
  token as required by the backend (typically the `csrftoken` cookie and
  matching `X-CSRFToken` header).
- The signed-in user must have `is_staff = true`. This is the backend's
  organizer check; ordinary members cannot create event posts.
- The caller does not have to be the event's admin. The new post is attributed
  to the event's admin, regardless of which staff user made the request.

## Path parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `event_id` | integer | Yes | ID of the event that will receive the post. |

## Request

Send JSON with `Content-Type: application/json`.

```json
{
  "content": "Join us at the community meetup!"
}
```

| Field | Type | Required | Constraints |
|---|---|---:|---|
| `content` | string | Yes | Non-empty; maximum 1,000 characters. |

The endpoint only uses `content`. Post metadata is set by the backend:

- Author: the event's admin.
- Tag: `event`.
- Pinned: `false`.
- Anonymous: `false`.
- Images: none.
- Creation timestamp: the event's creation timestamp.

Do not send `tags`, `pinned`, or `anonymous` to customize the post; this
endpoint does not use caller-supplied values for those properties.

### Example using `fetch`

```javascript
const response = await fetch(
  `${API_BASE_URL}/event/${eventId}/create-event-post/`,
  {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({
      content: "Join us at the community meetup!",
    }),
  },
);

const data = await response.json();
```

`API_BASE_URL` is the backend origin, and `csrfToken` is the CSRF token used by
the frontend's session-auth flow.

## Successful response

Returns **201 Created**. `event_post` is the updated **event representation**,
not the post object. In particular, `event_post.id` is the event ID, and the
response does not include the new post's ID or content.

```json
{
  "message": "Event post created successfully",
  "event_post": {
    "id": 42,
    "title": "Community Meetup",
    "description": "Meet fellow members",
    "date": "2026-12-01",
    "time": "6:00 PM - 8:00 PM",
    "location": "Town Hall",
    "admin": {
      "id": 7,
      "full_name": "Event Organizer",
      "primary_organization": "Atria Coop",
      "profile_image": null,
      "is_verified": true
    },
    "participants": [],
    "isEnrolled": false,
    "created_at": "2026-10-10T14:30:00Z",
    "hasPost": true
  }
}
```

The values above are illustrative. `participants` contains the event's
participants, and `isEnrolled` is computed for the signed-in caller.

## Errors

| Status | Example response | When it occurs |
|---:|---|---|
| `401 Unauthorized` | `{"error":"Not authenticated"}` | There is no authenticated session. |
| `403 Forbidden` | `{"error":"Only organizers can create event posts"}` | The caller is authenticated but is not staff. |
| `400 Bad Request` | `{"content":["This field is required."]}` | `content` is missing or invalid (including blank or longer than 1,000 characters). Serializer validation errors are returned by field. |
| `400 Bad Request` | `{"error":"Event with id 999 does not exist."}` | The event ID does not exist. |
| `400 Bad Request` | `{"error":"Event post already exists."}` | The event already has a linked post. |

The missing-event and duplicate-post messages are returned in the `error`
field; their exact string formatting may include Django's validation-error
representation.

## Update an event post

Updates the post linked to an existing event. This edits the post through the
events endpoint; it does not create a post if the event has none.

```http
PATCH /event/{event_id}/update_event_post/
```

The route is mounted at the backend root. Keep the underscore in
`update_event_post` and include the trailing slash.

In Django URL configuration, this route is named `event_update_post` and maps
the `PATCH` method to `EventViewSet.update_event_post`.

### Authorization

- The caller must be authenticated using session authentication and provide
  the CSRF token as described above.
- Only the event's admin can edit its linked post. A different staff user is
  not allowed unless that user is also the event admin.

### Request

Send a partial JSON object with `Content-Type: application/json`. This endpoint
only updates the post's content:

| Field | Type | Constraints |
|---|---|---|
| `content` | string | Maximum 1,000 characters; may be omitted for a partial update. |

Example:

```json
{
  "content": "Updated event announcement."
}
```

Example using `fetch`:

```javascript
const response = await fetch(
  `${API_BASE_URL}/event/${eventId}/update_event_post/`,
  {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({
      content: "Updated event announcement.",
    }),
  },
);

const data = await response.json();
```

### Success response

When the update succeeds, the endpoint returns **200 OK**. As with creation,
`event_post` is the updated event representation, not the post object:

```json
{
  "message": "Event post updated successfully",
  "event_post": {
    "id": 42,
    "title": "Community Meetup",
    "description": "Meet fellow members",
    "date": "2026-12-01",
    "time": "6:00 PM - 8:00 PM",
    "location": "Town Hall",
    "admin": {
      "id": 7,
      "full_name": "Event Organizer",
      "primary_organization": "Atria Coop",
      "profile_image": null,
      "is_verified": true
    },
    "participants": [],
    "isEnrolled": false,
    "created_at": "2026-10-10T14:30:00Z",
    "hasPost": true
  }
}
```

### Update errors and behavior

Validation and permission errors include:

| Status | Example response | When it occurs |
|---:|---|---|
| `401 Unauthorized` | `{"error":"Not authenticated"}` | There is no authenticated session. |
| `403 Forbidden` | `{"error":"Only the event organizer can edit this event"}` | The caller is not the event admin. |
| `400 Bad Request` | `{"error":"Event with id 999 does not exist."}` | The event ID does not exist. |
| `400 Bad Request` | `{"error":"Event post does not exist."}` | The event has no linked post to update. |
| `400 Bad Request` | `{"content":["Ensure this field has no more than 1000 characters."]}` | A supplied field fails serializer validation. |

Fields omitted from the PATCH request remain unchanged. This route does not
change tags, pinned status, anonymity, or images; those properties are outside
the event-post update contract.
