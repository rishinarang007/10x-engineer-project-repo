"""Tests for PromptLab utility functions (utils.py).

Covers sort_prompts_by_date, filter_prompts_by_collection, search_prompts,
validate_prompt_content, and extract_variables per the testing rule.
"""

from datetime import datetime, timedelta
from typing import Optional

import pytest
from app.models import Prompt
from app.utils import (
    sort_prompts_by_date,
    filter_prompts_by_collection,
    search_prompts,
    validate_prompt_content,
    extract_variables,
)


def _make_prompt(
    prompt_id: str,
    title: str = "T",
    description: Optional[str] = None,
    collection_id: Optional[str] = None,
    created_at: Optional[datetime] = None,
) -> Prompt:
    return Prompt(
        id=prompt_id,
        title=title,
        content="content",
        description=description,
        collection_id=collection_id,
        created_at=created_at or datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# ============== sort_prompts_by_date ==============


class TestSortPromptsByDate:
    """Tests for sort_prompts_by_date."""

    def test_sort_prompts_by_date_empty_list(self):
        """Empty list → []."""
        result = sort_prompts_by_date([])
        assert result == []

    def test_sort_prompts_by_date_single_item(self):
        """Single item → unchanged (new list)."""
        p = _make_prompt("id-1")
        result = sort_prompts_by_date([p])
        assert result == [p]
        assert result is not [p]

    def test_sort_prompts_by_date_multiple_descending(self):
        """Multiple items, descending (default) → newest first."""
        base = datetime.utcnow()
        p1 = _make_prompt("id-1", created_at=base + timedelta(seconds=2))
        p2 = _make_prompt("id-2", created_at=base)
        p3 = _make_prompt("id-3", created_at=base + timedelta(seconds=1))
        result = sort_prompts_by_date([p2, p1, p3], descending=True)
        assert [r.id for r in result] == ["id-1", "id-3", "id-2"]

    def test_sort_prompts_by_date_multiple_ascending(self):
        """Multiple items, ascending → oldest first."""
        base = datetime.utcnow()
        p1 = _make_prompt("id-1", created_at=base + timedelta(seconds=2))
        p2 = _make_prompt("id-2", created_at=base)
        p3 = _make_prompt("id-3", created_at=base + timedelta(seconds=1))
        result = sort_prompts_by_date([p1, p2, p3], descending=False)
        assert [r.id for r in result] == ["id-2", "id-3", "id-1"]

    def test_sort_prompts_by_date_does_not_mutate(self):
        """Original list is not mutated."""
        p1 = _make_prompt("id-1")
        p2 = _make_prompt("id-2")
        orig = [p1, p2]
        result = sort_prompts_by_date(orig)
        assert orig == [p1, p2]
        assert result is not orig


# ============== filter_prompts_by_collection ==============


class TestFilterPromptsByCollection:
    """Tests for filter_prompts_by_collection."""

    def test_filter_prompts_by_collection_empty_list(self):
        """Empty list → []."""
        result = filter_prompts_by_collection([], "col-1")
        assert result == []

    def test_filter_prompts_by_collection_no_matches(self):
        """No matches → []."""
        p1 = _make_prompt("id-1", collection_id=None)
        p2 = _make_prompt("id-2", collection_id="col-2")
        result = filter_prompts_by_collection([p1, p2], "col-1")
        assert result == []

    def test_filter_prompts_by_collection_some_match(self):
        """Some match → filtered list."""
        p1 = _make_prompt("id-1", collection_id="col-1")
        p2 = _make_prompt("id-2", collection_id="col-2")
        p3 = _make_prompt("id-3", collection_id="col-1")
        result = filter_prompts_by_collection([p1, p2, p3], "col-1")
        assert len(result) == 2
        assert {r.id for r in result} == {"id-1", "id-3"}

    def test_filter_prompts_by_collection_all_match(self):
        """All match → full list."""
        p1 = _make_prompt("id-1", collection_id="col-1")
        p2 = _make_prompt("id-2", collection_id="col-1")
        result = filter_prompts_by_collection([p1, p2], "col-1")
        assert len(result) == 2

    def test_filter_prompts_by_collection_excludes_none(self):
        """Prompts with collection_id=None never included."""
        p = _make_prompt("id-1", collection_id=None)
        result = filter_prompts_by_collection([p], "col-1")
        assert result == []


# ============== search_prompts ==============


class TestSearchPrompts:
    """Tests for search_prompts."""

    def test_search_prompts_empty_list(self):
        """Empty list → []."""
        result = search_prompts([], "query")
        assert result == []

    def test_search_prompts_no_match(self):
        """No match → []."""
        p = _make_prompt("id-1", title="Code Review", description="Review tasks")
        result = search_prompts([p], "xyznonexistent")
        assert result == []

    def test_search_prompts_match_title(self):
        """Match title → filtered."""
        p1 = _make_prompt("id-1", title="Code Review Master")
        p2 = _make_prompt("id-2", title="Unrelated")
        result = search_prompts([p1, p2], "master")
        assert len(result) == 1
        assert result[0].id == "id-1"

    def test_search_prompts_match_description(self):
        """Match description → filtered."""
        p1 = _make_prompt("id-1", title="X", description="Used for summarisation")
        p2 = _make_prompt("id-2", title="Y", description="Something else")
        result = search_prompts([p1, p2], "summarisation")
        assert len(result) == 1
        assert result[0].id == "id-1"

    def test_search_prompts_case_insensitive(self):
        """Case-insensitive matching."""
        p = _make_prompt("id-1", title="CODE REVIEW")
        result = search_prompts([p], "code")
        assert len(result) == 1

    def test_search_prompts_match_title_without_description(self):
        """Prompt without description: match title only."""
        p = _make_prompt("id-1", title="Special Title", description=None)
        result = search_prompts([p], "special")
        assert len(result) == 1


# ============== validate_prompt_content ==============


class TestValidatePromptContent:
    """Tests for validate_prompt_content."""

    def test_validate_prompt_content_none(self):
        """None → False."""
        assert validate_prompt_content(None) is False

    def test_validate_prompt_content_empty(self):
        """Empty string → False."""
        assert validate_prompt_content("") is False

    def test_validate_prompt_content_whitespace_only(self):
        """Whitespace only → False."""
        assert validate_prompt_content("   ") is False
        assert validate_prompt_content("\t\n") is False

    def test_validate_prompt_content_too_short(self):
        """Invalid (too short) → False."""
        assert validate_prompt_content("Short") is False
        assert validate_prompt_content("123456789") is False

    def test_validate_prompt_content_valid(self):
        """Valid → True."""
        assert validate_prompt_content("Summarize the article: {{text}}") is True
        assert validate_prompt_content("1234567890") is True


# ============== extract_variables ==============


class TestExtractVariables:
    """Tests for extract_variables."""

    def test_extract_variables_no_match(self):
        """No match → []."""
        result = extract_variables("No variables here.")
        assert result == []

    def test_extract_variables_single_match(self):
        """Single match → correct extraction."""
        result = extract_variables("Hello {{name}}!")
        assert result == ["name"]

    def test_extract_variables_multiple_matches(self):
        """Multiple matches → correct order."""
        result = extract_variables("Hello {{name}}, welcome to {{place}}!")
        assert result == ["name", "place"]

    def test_extract_variables_duplicates_preserved(self):
        """Duplicates preserved."""
        result = extract_variables("{{x}} and {{x}} again")
        assert result == ["x", "x"]

    def test_extract_variables_word_chars_only(self):
        """Only word chars (letters, digits, underscore) inside braces."""
        result = extract_variables("{{var_1}} and {{VAR2}}")
        assert result == ["var_1", "VAR2"]
