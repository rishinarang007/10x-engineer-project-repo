"""In-memory storage for PromptLab.

This module provides a simple, dictionary-backed storage layer for
prompts and collections. All data lives in process memory and is lost
when the server restarts. In a production environment this would be
replaced with a persistent database (e.g. PostgreSQL, SQLite).

Attributes:
    storage: The global ``Storage`` singleton used by the API layer.
"""

from typing import Dict, List, Optional, Set

from app.models import Prompt, Collection, Tag


class Storage:
    """In-memory data store for prompts and collections.

    Uses two dictionaries keyed by resource UUID to provide O(1) lookups
    by ID. A single ``Storage`` instance is created at module level and
    shared across the application.

    Attributes:
        _prompts: Internal dictionary mapping prompt IDs to ``Prompt``
            instances.
        _collections: Internal dictionary mapping collection IDs to
            ``Collection`` instances.
    """

    def __init__(self) -> None:
        """Initialise an empty storage instance.

        Both the prompt and collection stores start empty. Call
        ``clear()`` at any time to reset them back to this state.
        """
        self._prompts: Dict[str, Prompt] = {}
        self._collections: Dict[str, Collection] = {}
        self._tags: Dict[str, Tag] = {}
        self._tag_by_name: Dict[str, Tag] = {}
        self._prompt_tags: Dict[str, Set[str]] = {}

    # ============== Prompt Operations ==============

    def create_prompt(self, prompt: Prompt) -> Prompt:
        """Persist a new prompt.

        The prompt's ``id`` is used as the storage key. If a prompt with
        the same ID already exists it will be silently overwritten.

        Args:
            prompt: The fully constructed ``Prompt`` instance to store.

        Returns:
            The same ``Prompt`` instance that was passed in.
        """
        self._prompts[prompt.id] = prompt
        return prompt

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Retrieve a single prompt by ID.

        Args:
            prompt_id: The UUID of the prompt to look up.

        Returns:
            The matching ``Prompt`` if found, or ``None`` if the ID does
            not exist in the store.
        """
        return self._prompts.get(prompt_id)

    def get_all_prompts(self) -> List[Prompt]:
        """Retrieve every stored prompt.

        Returns:
            A list of all ``Prompt`` instances currently in the store.
            The order is not guaranteed.
        """
        return list(self._prompts.values())

    def update_prompt(self, prompt_id: str, prompt: Prompt) -> Optional[Prompt]:
        """Replace an existing prompt with an updated version.

        The prompt is only replaced if ``prompt_id`` already exists in
        the store. This prevents accidentally creating new entries
        through the update path.

        Args:
            prompt_id: The UUID of the prompt to replace.
            prompt: The new ``Prompt`` instance to store under the
                given ID.

        Returns:
            The updated ``Prompt`` on success, or ``None`` if no prompt
            with the given ID was found.
        """
        if prompt_id not in self._prompts:
            return None
        self._prompts[prompt_id] = prompt
        return prompt

    def delete_prompt(self, prompt_id: str) -> bool:
        """Remove a prompt from the store.

        Args:
            prompt_id: The UUID of the prompt to delete.

        Returns:
            ``True`` if the prompt existed and was deleted, ``False`` if
            no prompt with the given ID was found.
        """
        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            if prompt_id in self._prompt_tags:
                del self._prompt_tags[prompt_id]
            return True
        return False

    # ============== Tag Operations ==============

    def create_tag(self, tag: Tag) -> Tag:
        """Store a new tag.

        Args:
            tag: The Tag instance to store.

        Returns:
            The same Tag instance.
        """
        self._tags[tag.id] = tag
        self._tag_by_name[tag.name] = tag
        return tag

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """Retrieve a tag by ID."""
        return self._tags.get(tag_id)

    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """Retrieve a tag by normalised name."""
        return self._tag_by_name.get(name)

    def get_all_tags(self) -> List[Tag]:
        """Return all tags."""
        return list(self._tags.values())

    def delete_tag(self, tag_id: str) -> bool:
        """Remove a tag and all its prompt associations."""
        if tag_id not in self._tags:
            return False
        tag = self._tags[tag_id]
        del self._tags[tag_id]
        if tag.name in self._tag_by_name:
            del self._tag_by_name[tag.name]
        for prompt_id in list(self._prompt_tags.keys()):
            self._prompt_tags[prompt_id].discard(tag_id)
        return True

    def attach_tags(self, prompt_id: str, tag_ids: Set[str]) -> None:
        """Associate tags with a prompt (additive)."""
        if prompt_id not in self._prompt_tags:
            self._prompt_tags[prompt_id] = set()
        self._prompt_tags[prompt_id].update(tag_ids)

    def detach_tags(self, prompt_id: str, tag_ids: Set[str]) -> None:
        """Remove tag associations from a prompt."""
        if prompt_id in self._prompt_tags:
            self._prompt_tags[prompt_id] -= tag_ids

    def set_tags(self, prompt_id: str, tag_ids: Set[str]) -> None:
        """Replace all tags on a prompt."""
        self._prompt_tags[prompt_id] = set(tag_ids)

    def get_tags_for_prompt(self, prompt_id: str) -> List[Tag]:
        """Return tags attached to a prompt, sorted by name."""
        tag_ids = self._prompt_tags.get(prompt_id, set())
        tags = [self._tags[tid] for tid in tag_ids if tid in self._tags]
        return sorted(tags, key=lambda t: t.name)

    def get_prompt_count_for_tag(self, tag_id: str) -> int:
        """Count prompts carrying a tag."""
        return sum(1 for tids in self._prompt_tags.values() if tag_id in tids)

    def get_prompt_ids_by_tag(self, tag_id: str) -> Set[str]:
        """Return prompt IDs carrying a tag."""
        return {pid for pid, tids in self._prompt_tags.items() if tag_id in tids}

    # ============== Collection Operations ==============

    def create_collection(self, collection: Collection) -> Collection:
        """Persist a new collection.

        The collection's ``id`` is used as the storage key. If a
        collection with the same ID already exists it will be silently
        overwritten.

        Args:
            collection: The fully constructed ``Collection`` instance to
                store.

        Returns:
            The same ``Collection`` instance that was passed in.
        """
        self._collections[collection.id] = collection
        return collection

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Retrieve a single collection by ID.

        Args:
            collection_id: The UUID of the collection to look up.

        Returns:
            The matching ``Collection`` if found, or ``None`` if the ID
            does not exist in the store.
        """
        return self._collections.get(collection_id)

    def get_all_collections(self) -> List[Collection]:
        """Retrieve every stored collection.

        Returns:
            A list of all ``Collection`` instances currently in the
            store. The order is not guaranteed.
        """
        return list(self._collections.values())

    def delete_collection(self, collection_id: str) -> bool:
        """Remove a collection from the store.

        Note:
            This method only deletes the collection record itself. It
            does **not** cascade-delete prompts that reference this
            collection. Use the API-level ``delete_collection`` endpoint
            to handle cascading deletes.

        Args:
            collection_id: The UUID of the collection to delete.

        Returns:
            ``True`` if the collection existed and was deleted,
            ``False`` if no collection with the given ID was found.
        """
        if collection_id in self._collections:
            del self._collections[collection_id]
            return True
        return False

    def get_prompts_by_collection(self, collection_id: str) -> List[Prompt]:
        """Retrieve all prompts that belong to a specific collection.

        Scans every stored prompt and returns those whose
        ``collection_id`` matches the given value.

        Args:
            collection_id: The UUID of the target collection.

        Returns:
            A list of ``Prompt`` instances belonging to the collection.
            Returns an empty list if no prompts match.
        """
        return [
            p for p in self._prompts.values()
            if p.collection_id == collection_id
        ]

    # ============== Utility ==============

    def clear(self) -> None:
        """Remove all prompts, collections, and tags from the store.

        This resets the storage to its initial empty state. Primarily
        used by test fixtures to ensure a clean slate between tests.
        """
        self._prompts.clear()
        self._collections.clear()
        self._tags.clear()
        self._tag_by_name.clear()
        self._prompt_tags.clear()


# Global storage instance
storage = Storage()
