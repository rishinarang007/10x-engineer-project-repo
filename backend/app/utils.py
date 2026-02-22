"""Utility functions for PromptLab.

Pure helper functions used by the API layer for sorting, filtering,
searching, validating, and inspecting prompts. Every function in this
module is stateless and side-effect free.
"""

import re
from typing import List

from app.models import Prompt


def sort_prompts_by_date(
    prompts: List[Prompt],
    descending: bool = True,
) -> List[Prompt]:
    """Sort prompts by their creation date.

    Returns a **new** list; the original list is not mutated.

    Args:
        prompts: The prompts to sort.
        descending: Sort order. ``True`` (default) returns newest first;
            ``False`` returns oldest first.

    Returns:
        A new list of prompts sorted by ``created_at``.

    Example:
        >>> sorted_prompts = sort_prompts_by_date(prompts, descending=True)
        >>> sorted_prompts[0].created_at >= sorted_prompts[-1].created_at
        True
    """
    return sorted(prompts, key=lambda p: p.created_at, reverse=descending)


def filter_prompts_by_collection(
    prompts: List[Prompt],
    collection_id: str,
) -> List[Prompt]:
    """Filter prompts to only those belonging to a specific collection.

    Args:
        prompts: The full list of prompts to filter.
        collection_id: The UUID of the target collection.

    Returns:
        A list containing only the prompts whose ``collection_id``
        matches the given value. Prompts with ``collection_id = None``
        are never included.

    Example:
        >>> filtered = filter_prompts_by_collection(prompts, "abc-123")
        >>> all(p.collection_id == "abc-123" for p in filtered)
        True
    """
    return [p for p in prompts if p.collection_id == collection_id]


def filter_prompts_by_tags(
    prompts: List[Prompt],
    tag_names: List[str],
    match: str = "all",
) -> List[Prompt]:
    """Filter prompts by tag names.

    Args:
        prompts: The list of prompts to filter.
        tag_names: Tag names to match against (already normalised to
            lowercase).
        match: "all" requires every tag to be present; "any" requires
            at least one.

    Returns:
        Filtered list of prompts.
    """
    if not tag_names:
        return prompts
    tag_set = {n.lower() for n in tag_names}
    result = []
    for p in prompts:
        prompt_tag_names = {t.name.lower() for t in getattr(p, "tags", [])}
        if match == "any":
            if tag_set & prompt_tag_names:
                result.append(p)
        else:
            if tag_set <= prompt_tag_names:
                result.append(p)
    return result


def search_prompts(prompts: List[Prompt], query: str) -> List[Prompt]:
    """Search prompts by title and description (case-insensitive).

    A prompt matches if the query string appears as a substring in
    either its ``title`` or its ``description``. Prompts without a
    description are only matched against their title.

    Args:
        prompts: The list of prompts to search through.
        query: The search term. Matching is case-insensitive.

    Returns:
        A list of prompts that contain ``query`` in their title or
        description.

    Example:
        >>> results = search_prompts(prompts, "code review")
        >>> all("code review" in p.title.lower() or
        ...     (p.description and "code review" in p.description.lower())
        ...     for p in results)
        True
    """
    query_lower = query.lower()
    return [
        p for p in prompts
        if query_lower in p.title.lower()
        or (p.description and query_lower in p.description.lower())
    ]


def validate_prompt_content(content: str) -> bool:
    """Check whether prompt content meets minimum quality requirements.

    A valid prompt must:

    * Not be ``None`` or empty.
    * Not consist solely of whitespace.
    * Contain at least 10 non-whitespace-padded characters.

    Args:
        content: The raw prompt text to validate.

    Returns:
        ``True`` if the content passes all checks, ``False`` otherwise.

    Example:
        >>> validate_prompt_content("Short")
        False
        >>> validate_prompt_content("Summarize the following article: {{text}}")
        True
        >>> validate_prompt_content("   ")
        False
    """
    if not content or not content.strip():
        return False
    return len(content.strip()) >= 10


def extract_variables(content: str) -> List[str]:
    """Extract template variable names from prompt content.

    Variables follow the ``{{variable_name}}`` syntax. Only word
    characters (letters, digits, and underscores) are recognised
    inside the braces.

    Args:
        content: The prompt template string to scan.

    Returns:
        A list of variable names (without braces) in the order they
        appear. Duplicates are preserved if a variable is used more
        than once.

    Example:
        >>> extract_variables("Hello {{name}}, welcome to {{place}}!")
        ['name', 'place']
        >>> extract_variables("No variables here.")
        []
        >>> extract_variables("{{x}} and {{x}} again")
        ['x', 'x']
    """
    pattern = r"\{\{(\w+)\}\}"
    return re.findall(pattern, content)
