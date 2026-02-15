# PromptLab API Reference

> **Base URL:** `http://localhost:8000`
>
> **Interactive docs:** [Swagger UI](http://localhost:8000/docs) | [ReDoc](http://localhost:8000/redoc)
>
> **Content-Type:** All request and response bodies use `application/json`.

---

## Table of Contents

- [Authentication](#authentication)
- [Error Response Format](#error-response-format)
- [Validation Errors](#validation-errors)
- [Health](#health)
  - [GET /health](#get-health)
- [Prompts](#prompts)
  - [GET /prompts](#get-prompts)
  - [GET /prompts/{prompt_id}](#get-promptsprompt_id)
  - [POST /prompts](#post-prompts)
  - [PUT /prompts/{prompt_id}](#put-promptsprompt_id)
  - [PATCH /prompts/{prompt_id}](#patch-promptsprompt_id)
  - [DELETE /prompts/{prompt_id}](#delete-promptsprompt_id)
- [Collections](#collections)
  - [GET /collections](#get-collections)
  - [GET /collections/{collection_id}](#get-collectionscollection_id)
  - [POST /collections](#post-collections)
  - [DELETE /collections/{collection_id}](#delete-collectionscollection_id)

---

## Authentication

**None.** The API does not currently require any authentication or authorization. All endpoints are publicly accessible. This is suitable for local development and internal use only.

> **Future consideration:** Token-based authentication (e.g. API keys or OAuth 2.0 / JWT bearer tokens) should be added before deploying to any shared or production environment. When implemented, tokens will be passed via the `Authorization` header:
>
> ```
> Authorization: Bearer <token>
> ```

---

## Error Response Format

All error responses follow a consistent JSON structure:

```json
{
  "detail": "<human-readable error message>"
}
```

### Common HTTP Status Codes

| Status | Meaning                | When It Occurs                                  |
|--------|------------------------|-------------------------------------------------|
| 400    | Bad Request            | Invalid input or referenced resource not found  |
| 404    | Not Found              | The requested resource does not exist            |
| 422    | Unprocessable Entity   | Request body fails Pydantic validation           |

### Example -- 404 Not Found

```
GET /prompts/nonexistent-id
```

```json
{
  "detail": "Prompt not found"
}
```

### Example -- 400 Bad Request

```
POST /prompts
{
  "title": "My Prompt",
  "content": "Hello {{name}}",
  "collection_id": "nonexistent-collection-id"
}
```

```json
{
  "detail": "Collection not found"
}
```

---

## Validation Errors

When a request body fails Pydantic validation (e.g. missing required field, value too long), FastAPI returns **422 Unprocessable Entity** with a detailed error array:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": { "min_length": 1 }
    }
  ]
}
```

Each object in the `detail` array contains:

| Field   | Description                                            |
|---------|--------------------------------------------------------|
| `type`  | Machine-readable error type identifier                 |
| `loc`   | Path to the invalid field (e.g. `["body", "title"]`)   |
| `msg`   | Human-readable error message                           |
| `input` | The value that was received                            |
| `ctx`   | Additional context about the constraint that failed    |

---

## Health

### GET /health

Return the current health status and API version.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

| Field     | Type   | Description                               |
|-----------|--------|-------------------------------------------|
| `status`  | string | Service health status (e.g. `"healthy"`)  |
| `version` | string | Semantic version of the running API       |

**cURL:**

```bash
curl http://localhost:8000/health
```

---

## Prompts

A **Prompt** represents a reusable template for interacting with large language models. It supports `{{variable}}` placeholders.

### Prompt Object

| Field           | Type              | Description                                            |
|-----------------|-------------------|--------------------------------------------------------|
| `id`            | string (UUID)     | Unique identifier (server-generated)                   |
| `title`         | string            | Display name (1--200 characters, required)             |
| `content`       | string            | Prompt template text (min 1 character, required)       |
| `description`   | string \| null    | Short summary (max 500 characters, optional)           |
| `collection_id` | string \| null    | UUID of the parent collection, or `null`               |
| `created_at`    | string (datetime) | UTC creation timestamp (server-generated)              |
| `updated_at`    | string (datetime) | UTC last-modified timestamp (server-generated)         |

---

### GET /prompts

List all prompts with optional filtering and search. Results are sorted by creation date, newest first.

**Query Parameters:**

| Parameter       | Type   | Required | Description                                          |
|-----------------|--------|----------|------------------------------------------------------|
| `collection_id` | string | No       | Filter to prompts belonging to this collection UUID  |
| `search`        | string | No       | Case-insensitive substring search on title and description |

**Response:** `200 OK`

```json
{
  "prompts": [
    {
      "id": "a1c4d7e9-1234-5678-abcd-ef0123456789",
      "title": "Code Review Prompt",
      "content": "Review the following code:\n\n{{code}}",
      "description": "A prompt for AI code review",
      "collection_id": "b3e2a1f0-1234-5678-abcd-ef0123456789",
      "created_at": "2026-02-15T12:01:00.000000",
      "updated_at": "2026-02-15T12:01:00.000000"
    }
  ],
  "total": 1
}
```

**cURL:**

```bash
# List all prompts
curl http://localhost:8000/prompts

# Filter by collection
curl "http://localhost:8000/prompts?collection_id=b3e2a1f0-1234-5678-abcd-ef0123456789"

# Search by keyword
curl "http://localhost:8000/prompts?search=code+review"

# Combine filters
curl "http://localhost:8000/prompts?collection_id=b3e2a1f0-1234-5678-abcd-ef0123456789&search=review"
```

---

### GET /prompts/{prompt_id}

Retrieve a single prompt by ID.

**Path Parameters:**

| Parameter   | Type   | Description                  |
|-------------|--------|------------------------------|
| `prompt_id` | string | UUID of the prompt to fetch  |

**Response:** `200 OK`

```json
{
  "id": "a1c4d7e9-1234-5678-abcd-ef0123456789",
  "title": "Code Review Prompt",
  "content": "Review the following code:\n\n{{code}}",
  "description": "A prompt for AI code review",
  "collection_id": "b3e2a1f0-1234-5678-abcd-ef0123456789",
  "created_at": "2026-02-15T12:01:00.000000",
  "updated_at": "2026-02-15T12:01:00.000000"
}
```

**Error Response:** `404 Not Found`

```json
{
  "detail": "Prompt not found"
}
```

**cURL:**

```bash
curl http://localhost:8000/prompts/a1c4d7e9-1234-5678-abcd-ef0123456789
```

---

### POST /prompts

Create a new prompt.

**Request Body:**

| Field           | Type           | Required | Description                              |
|-----------------|----------------|----------|------------------------------------------|
| `title`         | string         | Yes      | Display name (1--200 characters)         |
| `content`       | string         | Yes      | Prompt template text (min 1 character)   |
| `description`   | string \| null | No       | Short summary (max 500 characters)       |
| `collection_id` | string \| null | No       | UUID of an existing collection           |

**Request Example:**

```json
{
  "title": "Code Review Prompt",
  "content": "Review the following code and provide feedback:\n\n{{code}}",
  "description": "A prompt for AI code review",
  "collection_id": "b3e2a1f0-1234-5678-abcd-ef0123456789"
}
```

**Response:** `201 Created`

```json
{
  "id": "a1c4d7e9-1234-5678-abcd-ef0123456789",
  "title": "Code Review Prompt",
  "content": "Review the following code and provide feedback:\n\n{{code}}",
  "description": "A prompt for AI code review",
  "collection_id": "b3e2a1f0-1234-5678-abcd-ef0123456789",
  "created_at": "2026-02-15T12:01:00.000000",
  "updated_at": "2026-02-15T12:01:00.000000"
}
```

**Error Response:** `400 Bad Request` (invalid collection)

```json
{
  "detail": "Collection not found"
}
```

**Error Response:** `422 Unprocessable Entity` (missing required field)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "title"],
      "msg": "Field required",
      "input": { "content": "Hello" }
    }
  ]
}
```

**cURL:**

```bash
curl -X POST http://localhost:8000/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Code Review Prompt",
    "content": "Review the following code and provide feedback:\n\n{{code}}",
    "description": "A prompt for AI code review"
  }'
```

---

### PUT /prompts/{prompt_id}

Fully replace an existing prompt. All mutable fields are overwritten. The `id` and `created_at` are preserved; `updated_at` is refreshed automatically.

**Path Parameters:**

| Parameter   | Type   | Description                    |
|-------------|--------|--------------------------------|
| `prompt_id` | string | UUID of the prompt to replace  |

**Request Body:**

| Field           | Type           | Required | Description                              |
|-----------------|----------------|----------|------------------------------------------|
| `title`         | string         | No*      | New title (1--200 characters)            |
| `content`       | string         | No*      | New prompt template text                 |
| `description`   | string \| null | No       | New description (max 500 characters)     |
| `collection_id` | string \| null | No       | New collection UUID, or `null`           |

> *All fields use the `PromptUpdate` model where every field is optional. However, for a full replacement (PUT), you should provide all fields to avoid setting them to `null`.

**Request Example:**

```json
{
  "title": "Updated Code Review Prompt",
  "content": "Please review this pull request:\n\n{{diff}}",
  "description": "Updated prompt for PR reviews",
  "collection_id": "b3e2a1f0-1234-5678-abcd-ef0123456789"
}
```

**Response:** `200 OK`

```json
{
  "id": "a1c4d7e9-1234-5678-abcd-ef0123456789",
  "title": "Updated Code Review Prompt",
  "content": "Please review this pull request:\n\n{{diff}}",
  "description": "Updated prompt for PR reviews",
  "collection_id": "b3e2a1f0-1234-5678-abcd-ef0123456789",
  "created_at": "2026-02-15T12:01:00.000000",
  "updated_at": "2026-02-15T12:05:00.000000"
}
```

**Error Responses:**

- `404 Not Found` -- prompt does not exist
- `400 Bad Request` -- referenced collection does not exist

**cURL:**

```bash
curl -X PUT http://localhost:8000/prompts/a1c4d7e9-1234-5678-abcd-ef0123456789 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Code Review Prompt",
    "content": "Please review this pull request:\n\n{{diff}}",
    "description": "Updated prompt for PR reviews",
    "collection_id": "b3e2a1f0-1234-5678-abcd-ef0123456789"
  }'
```

---

### PATCH /prompts/{prompt_id}

Partially update an existing prompt. Only fields included in the request body are modified; omitted fields remain unchanged. `updated_at` is refreshed when at least one field changes.

**Path Parameters:**

| Parameter   | Type   | Description                  |
|-------------|--------|------------------------------|
| `prompt_id` | string | UUID of the prompt to patch  |

**Request Body:**

All fields are optional. Include only the fields you want to change.

| Field           | Type           | Description                              |
|-----------------|----------------|------------------------------------------|
| `title`         | string         | New title (1--200 characters)            |
| `content`       | string         | New prompt template text                 |
| `description`   | string \| null | New description (max 500 characters)     |
| `collection_id` | string \| null | New collection UUID, or `null`           |

**Request Example (update description only):**

```json
{
  "description": "Improved description for the code review prompt"
}
```

**Response:** `200 OK`

```json
{
  "id": "a1c4d7e9-1234-5678-abcd-ef0123456789",
  "title": "Code Review Prompt",
  "content": "Review the following code and provide feedback:\n\n{{code}}",
  "description": "Improved description for the code review prompt",
  "collection_id": "b3e2a1f0-1234-5678-abcd-ef0123456789",
  "created_at": "2026-02-15T12:01:00.000000",
  "updated_at": "2026-02-15T12:10:00.000000"
}
```

**Response (empty body -- no changes):** `200 OK`

Returns the existing prompt unchanged.

**Error Responses:**

- `404 Not Found` -- prompt does not exist
- `400 Bad Request` -- referenced collection does not exist

**cURL:**

```bash
curl -X PATCH http://localhost:8000/prompts/a1c4d7e9-1234-5678-abcd-ef0123456789 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Improved description for the code review prompt"
  }'
```

---

### DELETE /prompts/{prompt_id}

Delete a prompt by ID.

**Path Parameters:**

| Parameter   | Type   | Description                   |
|-------------|--------|-------------------------------|
| `prompt_id` | string | UUID of the prompt to delete  |

**Response:** `204 No Content`

No response body.

**Error Response:** `404 Not Found`

```json
{
  "detail": "Prompt not found"
}
```

**cURL:**

```bash
curl -X DELETE http://localhost:8000/prompts/a1c4d7e9-1234-5678-abcd-ef0123456789
```

---

## Collections

A **Collection** is a named grouping of prompts, analogous to a folder or workspace.

### Collection Object

| Field         | Type              | Description                                    |
|---------------|-------------------|------------------------------------------------|
| `id`          | string (UUID)     | Unique identifier (server-generated)           |
| `name`        | string            | Display name (1--100 characters, required)     |
| `description` | string \| null    | Short summary (max 500 characters, optional)   |
| `created_at`  | string (datetime) | UTC creation timestamp (server-generated)      |

---

### GET /collections

List all collections.

**Response:** `200 OK`

```json
{
  "collections": [
    {
      "id": "b3e2a1f0-1234-5678-abcd-ef0123456789",
      "name": "Code Review",
      "description": "Prompts for reviewing code",
      "created_at": "2026-02-15T12:00:00.000000"
    }
  ],
  "total": 1
}
```

**cURL:**

```bash
curl http://localhost:8000/collections
```

---

### GET /collections/{collection_id}

Retrieve a single collection by ID.

**Path Parameters:**

| Parameter       | Type   | Description                      |
|-----------------|--------|----------------------------------|
| `collection_id` | string | UUID of the collection to fetch  |

**Response:** `200 OK`

```json
{
  "id": "b3e2a1f0-1234-5678-abcd-ef0123456789",
  "name": "Code Review",
  "description": "Prompts for reviewing code",
  "created_at": "2026-02-15T12:00:00.000000"
}
```

**Error Response:** `404 Not Found`

```json
{
  "detail": "Collection not found"
}
```

**cURL:**

```bash
curl http://localhost:8000/collections/b3e2a1f0-1234-5678-abcd-ef0123456789
```

---

### POST /collections

Create a new collection.

**Request Body:**

| Field         | Type           | Required | Description                            |
|---------------|----------------|----------|----------------------------------------|
| `name`        | string         | Yes      | Display name (1--100 characters)       |
| `description` | string \| null | No       | Short summary (max 500 characters)     |

**Request Example:**

```json
{
  "name": "Code Review",
  "description": "Prompts for reviewing code"
}
```

**Response:** `201 Created`

```json
{
  "id": "b3e2a1f0-1234-5678-abcd-ef0123456789",
  "name": "Code Review",
  "description": "Prompts for reviewing code",
  "created_at": "2026-02-15T12:00:00.000000"
}
```

**Error Response:** `422 Unprocessable Entity` (missing required field)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

**cURL:**

```bash
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Review",
    "description": "Prompts for reviewing code"
  }'
```

---

### DELETE /collections/{collection_id}

Delete a collection **and all prompts that belong to it**. This is a cascading delete -- any prompt whose `collection_id` matches the deleted collection will also be removed.

**Path Parameters:**

| Parameter       | Type   | Description                       |
|-----------------|--------|-----------------------------------|
| `collection_id` | string | UUID of the collection to delete  |

**Response:** `204 No Content`

No response body.

**Error Response:** `404 Not Found`

```json
{
  "detail": "Collection not found"
}
```

**cURL:**

```bash
curl -X DELETE http://localhost:8000/collections/b3e2a1f0-1234-5678-abcd-ef0123456789
```
