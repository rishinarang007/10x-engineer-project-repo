"""Pydantic models for PromptLab.

This module defines all request and response models used by the PromptLab API.
Models leverage Pydantic v2 for runtime data validation, serialization, and
automatic OpenAPI schema generation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import uuid4


def generate_id() -> str:
    """Generate a unique identifier for a resource.

    Creates a UUID4 string to serve as the primary key for prompts
    and collections.

    Returns:
        A UUID4 string (e.g. ``"b3e2a1f0-7c8d-4e9a-af12-3b4c5d6e7f89"``).
    """
    return str(uuid4())


def get_current_time() -> datetime:
    """Return the current UTC timestamp.

    Used as the default factory for ``created_at`` and ``updated_at``
    fields on resource models.

    Returns:
        A timezone-naive ``datetime`` representing the current UTC time.
    """
    return datetime.utcnow()


# ============== Prompt Models ==============


class PromptBase(BaseModel):
    """Base schema shared by all prompt-related models.

    Contains the core fields that every prompt must have when being
    created or returned from the API.

    Attributes:
        title: The display name of the prompt. Must be between 1 and
            200 characters.
        content: The full prompt template text. Supports ``{{variable}}``
            placeholders. Must be at least 1 character.
        description: An optional short summary of what the prompt does.
            Maximum 500 characters.
        collection_id: An optional UUID referencing the collection this
            prompt belongs to. ``None`` means the prompt is uncategorized.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name of the prompt (1-200 characters).",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Full prompt template text. Supports {{variable}} placeholders.",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional short summary of the prompt (max 500 characters).",
    )
    collection_id: Optional[str] = Field(
        None,
        description="UUID of the collection this prompt belongs to, or null if uncategorized.",
    )


class PromptCreate(PromptBase):
    """Request body for creating a new prompt.

    Inherits all fields from ``PromptBase``. No additional fields are
    required; the server generates ``id``, ``created_at``, and
    ``updated_at`` automatically.
    """

    pass


class PromptUpdate(BaseModel):
    """Request body for updating an existing prompt.

    All fields are optional so that clients can perform both full
    replacements (PUT) and partial patches (PATCH). Fields that are
    not included in the request body remain unchanged on the server.

    Attributes:
        title: New title for the prompt. Must be between 1 and 200
            characters if provided.
        content: New prompt template text if provided. Must be at least
            1 character.
        description: New description if provided. Maximum 500 characters.
        collection_id: New collection UUID, or ``None`` to remove the
            prompt from its current collection.
    """

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="New title for the prompt (1-200 characters).",
    )
    content: Optional[str] = Field(
        None,
        min_length=1,
        description="New prompt template text.",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="New description (max 500 characters).",
    )
    collection_id: Optional[str] = Field(
        None,
        description="New collection UUID, or null to uncategorize the prompt.",
    )


class Prompt(PromptBase):
    """Complete prompt resource returned by the API.

    Extends ``PromptBase`` with server-generated metadata fields that
    are set automatically when a prompt is created or updated.

    Attributes:
        id: Unique identifier for the prompt, generated as a UUID4.
        created_at: UTC timestamp of when the prompt was first created.
        updated_at: UTC timestamp of the most recent modification.
    """

    id: str = Field(
        default_factory=generate_id,
        description="Unique UUID4 identifier for the prompt.",
    )
    created_at: datetime = Field(
        default_factory=get_current_time,
        description="UTC timestamp of when the prompt was created.",
    )
    updated_at: datetime = Field(
        default_factory=get_current_time,
        description="UTC timestamp of the last modification.",
    )

    class Config:
        """Pydantic model configuration.

        Attributes:
            from_attributes: Allow population of the model from ORM-style
                attribute access (e.g. SQLAlchemy rows).
        """

        from_attributes = True


# ============== Collection Models ==============


class CollectionBase(BaseModel):
    """Base schema shared by all collection-related models.

    A collection is a named grouping of prompts, analogous to a folder.

    Attributes:
        name: The display name of the collection. Must be between 1 and
            100 characters.
        description: An optional summary of the collection's purpose.
            Maximum 500 characters.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name of the collection (1-100 characters).",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional summary of the collection (max 500 characters).",
    )


class CollectionCreate(CollectionBase):
    """Request body for creating a new collection.

    Inherits all fields from ``CollectionBase``. The server generates
    ``id`` and ``created_at`` automatically.
    """

    pass


class Collection(CollectionBase):
    """Complete collection resource returned by the API.

    Extends ``CollectionBase`` with server-generated metadata.

    Attributes:
        id: Unique identifier for the collection, generated as a UUID4.
        created_at: UTC timestamp of when the collection was created.
    """

    id: str = Field(
        default_factory=generate_id,
        description="Unique UUID4 identifier for the collection.",
    )
    created_at: datetime = Field(
        default_factory=get_current_time,
        description="UTC timestamp of when the collection was created.",
    )

    class Config:
        """Pydantic model configuration.

        Attributes:
            from_attributes: Allow population of the model from ORM-style
                attribute access (e.g. SQLAlchemy rows).
        """

        from_attributes = True


# ============== Response Models ==============


class PromptList(BaseModel):
    """Paginated response containing a list of prompts.

    Attributes:
        prompts: The list of prompt resources matching the request.
        total: Total number of prompts in the result set.
    """

    prompts: List[Prompt] = Field(
        ...,
        description="List of prompt resources.",
    )
    total: int = Field(
        ...,
        description="Total number of prompts in the result set.",
    )


class CollectionList(BaseModel):
    """Paginated response containing a list of collections.

    Attributes:
        collections: The list of collection resources.
        total: Total number of collections in the result set.
    """

    collections: List[Collection] = Field(
        ...,
        description="List of collection resources.",
    )
    total: int = Field(
        ...,
        description="Total number of collections in the result set.",
    )


class HealthResponse(BaseModel):
    """Response model for the ``/health`` endpoint.

    Attributes:
        status: Current health status of the service
            (e.g. ``"healthy"``).
        version: Semantic version string of the running API
            (e.g. ``"0.1.0"``).
    """

    status: str = Field(
        ...,
        description="Current health status of the service (e.g. 'healthy').",
    )
    version: str = Field(
        ...,
        description="Semantic version of the running API (e.g. '0.1.0').",
    )
