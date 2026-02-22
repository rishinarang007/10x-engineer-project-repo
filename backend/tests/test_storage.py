"""Tests for PromptLab storage layer (storage.py).

Covers Storage class methods per the testing rule's edge-case checklist.
"""

from typing import Optional
import pytest
from app.models import Prompt, Collection
from app.storage import Storage


@pytest.fixture
def store():
    """Fresh Storage instance for isolation."""
    return Storage()


def _make_prompt(prompt_id: str, collection_id: Optional[str] = None) -> Prompt:
    return Prompt(
        id=prompt_id,
        title="T",
        content="C",
        description=None,
        collection_id=collection_id,
    )


def _make_collection(collection_id: str) -> Collection:
    return Collection(id=collection_id, name="N", description=None)


# ============== Prompt Operations ==============


class TestStorageGetPrompt:
    """Tests for get_prompt (single lookup)."""

    def test_get_prompt_id_exists(self, store: Storage):
        """ID exists → return resource."""
        p = _make_prompt("id-1")
        store.create_prompt(p)
        result = store.get_prompt("id-1")
        assert result is not None
        assert result.id == "id-1"
        assert result.title == "T"

    def test_get_prompt_id_not_in_store(self, store: Storage):
        """ID not in store → None."""
        result = store.get_prompt("nonexistent")
        assert result is None

    def test_get_prompt_empty_string(self, store: Storage):
        """Empty string / unknown key → None."""
        result = store.get_prompt("")
        assert result is None


class TestStorageCreatePrompt:
    """Tests for create_prompt."""

    def test_create_prompt_valid(self, store: Storage):
        """Valid resource → return stored resource."""
        p = _make_prompt("id-1")
        result = store.create_prompt(p)
        assert result is p
        assert store.get_prompt("id-1") is p

    def test_create_prompt_same_id_overwrites(self, store: Storage):
        """Same ID already exists → overwrite, return."""
        p1 = _make_prompt("id-1")
        p2 = _make_prompt("id-1")
        p2.title = "Updated"
        store.create_prompt(p1)
        result = store.create_prompt(p2)
        assert result is p2
        assert store.get_prompt("id-1").title == "Updated"


class TestStorageUpdatePrompt:
    """Tests for update_prompt."""

    def test_update_prompt_id_exists(self, store: Storage):
        """ID exists → return updated resource."""
        p = _make_prompt("id-1")
        store.create_prompt(p)
        p2 = _make_prompt("id-1")
        p2.title = "Updated"
        result = store.update_prompt("id-1", p2)
        assert result is p2
        assert store.get_prompt("id-1").title == "Updated"

    def test_update_prompt_id_not_in_store(self, store: Storage):
        """ID not in store → None."""
        p = _make_prompt("id-1")
        result = store.update_prompt("nonexistent", p)
        assert result is None
        assert store.get_prompt("id-1") is None


class TestStorageDeletePrompt:
    """Tests for delete_prompt."""

    def test_delete_prompt_id_exists(self, store: Storage):
        """ID exists → True."""
        p = _make_prompt("id-1")
        store.create_prompt(p)
        result = store.delete_prompt("id-1")
        assert result is True
        assert store.get_prompt("id-1") is None

    def test_delete_prompt_id_not_in_store(self, store: Storage):
        """ID not in store → False."""
        result = store.delete_prompt("nonexistent")
        assert result is False


class TestStorageGetAllPrompts:
    """Tests for get_all_prompts."""

    def test_get_all_prompts_empty_store(self, store: Storage):
        """Empty store → []."""
        result = store.get_all_prompts()
        assert result == []

    def test_get_all_prompts_with_items(self, store: Storage):
        """With items → list of all."""
        p1 = _make_prompt("id-1")
        p2 = _make_prompt("id-2")
        store.create_prompt(p1)
        store.create_prompt(p2)
        result = store.get_all_prompts()
        assert len(result) == 2
        ids = {r.id for r in result}
        assert ids == {"id-1", "id-2"}


# ============== Collection Operations ==============


class TestStorageGetCollection:
    """Tests for get_collection."""

    def test_get_collection_id_exists(self, store: Storage):
        """ID exists → return resource."""
        c = _make_collection("col-1")
        store.create_collection(c)
        result = store.get_collection("col-1")
        assert result is not None
        assert result.id == "col-1"

    def test_get_collection_id_not_in_store(self, store: Storage):
        """ID not in store → None."""
        result = store.get_collection("nonexistent")
        assert result is None


class TestStorageCreateCollection:
    """Tests for create_collection."""

    def test_create_collection_valid(self, store: Storage):
        """Valid resource → return stored resource."""
        c = _make_collection("col-1")
        result = store.create_collection(c)
        assert result is c
        assert store.get_collection("col-1") is c

    def test_create_collection_same_id_overwrites(self, store: Storage):
        """Same ID already exists → overwrite, return."""
        c1 = _make_collection("col-1")
        c2 = _make_collection("col-1")
        c2.name = "Updated"
        store.create_collection(c1)
        result = store.create_collection(c2)
        assert result is c2
        assert store.get_collection("col-1").name == "Updated"


class TestStorageDeleteCollection:
    """Tests for delete_collection."""

    def test_delete_collection_id_exists(self, store: Storage):
        """ID exists → True."""
        c = _make_collection("col-1")
        store.create_collection(c)
        result = store.delete_collection("col-1")
        assert result is True
        assert store.get_collection("col-1") is None

    def test_delete_collection_id_not_in_store(self, store: Storage):
        """ID not in store → False."""
        result = store.delete_collection("nonexistent")
        assert result is False


class TestStorageGetAllCollections:
    """Tests for get_all_collections."""

    def test_get_all_collections_empty_store(self, store: Storage):
        """Empty store → []."""
        result = store.get_all_collections()
        assert result == []

    def test_get_all_collections_with_items(self, store: Storage):
        """With items → list of all."""
        c1 = _make_collection("col-1")
        c2 = _make_collection("col-2")
        store.create_collection(c1)
        store.create_collection(c2)
        result = store.get_all_collections()
        assert len(result) == 2


class TestStorageGetPromptsByCollection:
    """Tests for get_prompts_by_collection (filter)."""

    def test_get_prompts_by_collection_no_matches(self, store: Storage):
        """No matches → []."""
        p = _make_prompt("id-1", collection_id=None)
        store.create_prompt(p)
        result = store.get_prompts_by_collection("col-1")
        assert result == []

    def test_get_prompts_by_collection_some_match(self, store: Storage):
        """Some match → filtered list."""
        p1 = _make_prompt("id-1", collection_id="col-1")
        p2 = _make_prompt("id-2", collection_id="col-2")
        p3 = _make_prompt("id-3", collection_id="col-1")
        store.create_prompt(p1)
        store.create_prompt(p2)
        store.create_prompt(p3)
        result = store.get_prompts_by_collection("col-1")
        assert len(result) == 2
        assert {r.id for r in result} == {"id-1", "id-3"}

    def test_get_prompts_by_collection_all_match(self, store: Storage):
        """All match → full list."""
        p1 = _make_prompt("id-1", collection_id="col-1")
        p2 = _make_prompt("id-2", collection_id="col-1")
        store.create_prompt(p1)
        store.create_prompt(p2)
        result = store.get_prompts_by_collection("col-1")
        assert len(result) == 2


class TestStorageClear:
    """Tests for clear."""

    def test_clear_empty_store(self, store: Storage):
        """Any state → empty store."""
        store.clear()
        assert store.get_all_prompts() == []
        assert store.get_all_collections() == []

    def test_clear_with_data(self, store: Storage):
        """With data → empty after clear."""
        store.create_prompt(_make_prompt("id-1"))
        store.create_collection(_make_collection("col-1"))
        store.clear()
        assert store.get_all_prompts() == []
        assert store.get_all_collections() == []
        assert store.get_prompt("id-1") is None
        assert store.get_collection("col-1") is None
