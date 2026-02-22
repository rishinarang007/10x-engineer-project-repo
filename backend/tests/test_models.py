"""Tests for PromptLab models (models.py).

Covers generate_id, get_current_time, and Pydantic model validation.
"""

import re
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models import (
    generate_id,
    get_current_time,
    Prompt,
    PromptCreate,
    PromptUpdate,
    Collection,
    CollectionCreate,
    PromptList,
    CollectionList,
    HealthResponse,
)


# UUID pattern (8-4-4-4-12 hex)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


# ============== Helper Functions ==============


class TestGenerateId:
    """Tests for generate_id()."""

    def test_generate_id_returns_string(self):
        """Each call returns a string."""
        result = generate_id()
        assert isinstance(result, str)
        assert len(result) == 36

    def test_generate_id_valid_uuid_format(self):
        """Format: 8-4-4-4-12 hex segments."""
        result = generate_id()
        assert UUID_PATTERN.match(result)

    def test_generate_id_unique_per_call(self):
        """Each call produces a unique ID."""
        ids = [generate_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestGetCurrentTime:
    """Tests for get_current_time()."""

    def test_get_current_time_returns_datetime(self):
        """Call returns datetime instance."""
        result = get_current_time()
        assert isinstance(result, datetime)
        assert result is not None

    def test_get_current_time_is_utc(self):
        """Returns UTC (tzinfo is None for naive UTC)."""
        result = get_current_time()
        assert result.tzinfo is None


# ============== Prompt Models ==============


class TestPromptCreate:
    """Tests for PromptCreate validation."""

    def test_prompt_create_valid(self):
        """Valid required fields → instance created."""
        data = {"title": "T", "content": "C"}
        p = PromptCreate(**data)
        assert p.title == "T"
        assert p.content == "C"
        assert p.description is None
        assert p.collection_id is None

    def test_prompt_create_missing_title_raises(self):
        """Missing required field (title) → ValidationError."""
        with pytest.raises(ValidationError):
            PromptCreate(content="C")

    def test_prompt_create_missing_content_raises(self):
        """Missing required field (content) → ValidationError."""
        with pytest.raises(ValidationError):
            PromptCreate(title="T")

    def test_prompt_create_empty_title_raises(self):
        """Empty string for title (min_length=1) → ValidationError."""
        with pytest.raises(ValidationError):
            PromptCreate(title="", content="C")

    def test_prompt_create_empty_content_raises(self):
        """Empty string for content (min_length=1) → ValidationError."""
        with pytest.raises(ValidationError):
            PromptCreate(title="T", content="")

    def test_prompt_create_title_exceeds_max_raises(self):
        """Title exceeds max_length=200 → ValidationError."""
        with pytest.raises(ValidationError):
            PromptCreate(title="x" * 201, content="C")

    def test_prompt_create_description_exceeds_max_raises(self):
        """Description exceeds max_length=500 → ValidationError."""
        with pytest.raises(ValidationError):
            PromptCreate(title="T", content="C", description="x" * 501)

    def test_prompt_create_invalid_type_title_raises(self):
        """Wrong type for title → ValidationError."""
        with pytest.raises(ValidationError):
            PromptCreate(title=123, content="C")

    def test_prompt_create_with_optional_fields(self):
        """Optional description and collection_id accepted."""
        p = PromptCreate(
            title="T",
            content="C",
            description="D",
            collection_id="00000000-0000-0000-0000-000000000000",
        )
        assert p.description == "D"
        assert p.collection_id == "00000000-0000-0000-0000-000000000000"


class TestPromptUpdate:
    """Tests for PromptUpdate validation (all optional)."""

    def test_prompt_update_empty_dict(self):
        """Empty dict → instance with all None."""
        p = PromptUpdate()
        assert p.title is None
        assert p.content is None
        assert p.description is None
        assert p.collection_id is None

    def test_prompt_update_partial_fields(self):
        """Partial fields → instance with provided only."""
        p = PromptUpdate(title="New")
        assert p.title == "New"
        assert p.content is None

    def test_prompt_update_empty_title_when_provided_raises(self):
        """Empty title when provided (min_length=1) → ValidationError."""
        with pytest.raises(ValidationError):
            PromptUpdate(title="")

    def test_prompt_update_empty_content_when_provided_raises(self):
        """Empty content when provided (min_length=1) → ValidationError."""
        with pytest.raises(ValidationError):
            PromptUpdate(content="")


class TestPrompt:
    """Tests for Prompt (full resource model)."""

    def test_prompt_default_factories(self):
        """id, created_at, updated_at auto-populated."""
        p = Prompt(title="T", content="C")
        assert p.id is not None
        assert len(p.id) == 36
        assert UUID_PATTERN.match(p.id)
        assert p.created_at is not None
        assert p.updated_at is not None
        assert isinstance(p.created_at, datetime)

    def test_prompt_model_dump(self):
        """model_dump() produces JSON-serializable dict."""
        p = Prompt(title="T", content="C")
        d = p.model_dump()
        assert "id" in d
        assert "title" in d
        assert "content" in d
        assert "created_at" in d
        assert "updated_at" in d

    def test_prompt_model_copy_update(self):
        """model_copy(update=...) performs partial merge."""
        p = Prompt(title="T", content="C")
        p2 = p.model_copy(update={"title": "Updated"})
        assert p2.title == "Updated"
        assert p2.content == "C"
        assert p2.id == p.id


# ============== Collection Models ==============


class TestCollectionCreate:
    """Tests for CollectionCreate validation."""

    def test_collection_create_valid(self):
        """Valid required field (name) → instance created."""
        c = CollectionCreate(name="N")
        assert c.name == "N"
        assert c.description is None

    def test_collection_create_missing_name_raises(self):
        """Missing required field (name) → ValidationError."""
        with pytest.raises(ValidationError):
            CollectionCreate()

    def test_collection_create_empty_name_raises(self):
        """Empty name (min_length=1) → ValidationError."""
        with pytest.raises(ValidationError):
            CollectionCreate(name="")

    def test_collection_create_name_exceeds_max_raises(self):
        """Name exceeds max_length=100 → ValidationError."""
        with pytest.raises(ValidationError):
            CollectionCreate(name="x" * 101)


class TestCollection:
    """Tests for Collection (full resource model)."""

    def test_collection_default_factories(self):
        """id, created_at auto-populated."""
        c = Collection(name="N")
        assert c.id is not None
        assert UUID_PATTERN.match(c.id)
        assert c.created_at is not None


# ============== Response Models ==============


class TestPromptList:
    """Tests for PromptList."""

    def test_prompt_list_valid(self):
        """Valid prompts and total → instance created."""
        pl = PromptList(prompts=[], total=0)
        assert pl.prompts == []
        assert pl.total == 0

    def test_prompt_list_missing_prompts_raises(self):
        """Missing required field → ValidationError."""
        with pytest.raises(ValidationError):
            PromptList(total=0)


class TestCollectionList:
    """Tests for CollectionList."""

    def test_collection_list_valid(self):
        """Valid collections and total → instance created."""
        cl = CollectionList(collections=[], total=0)
        assert cl.collections == []
        assert cl.total == 0


class TestHealthResponse:
    """Tests for HealthResponse."""

    def test_health_response_valid(self):
        """Valid status and version → instance created."""
        h = HealthResponse(status="healthy", version="0.1.0")
        assert h.status == "healthy"
        assert h.version == "0.1.0"
