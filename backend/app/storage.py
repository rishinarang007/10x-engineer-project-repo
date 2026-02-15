"""In-memory storage for PromptLab.

This module provides a simple, dictionary-backed storage layer for
prompts and collections. All data lives in process memory and is lost
when the server restarts. In a production environment this would be
replaced with a persistent database (e.g. PostgreSQL, SQLite).

Attributes:
    storage: The global ``Storage`` singleton used by the API layer.
"""

from typing import Dict, List, Optional

from app.models import Prompt, Collection


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
            return True
        return False

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
        """Remove all prompts and collections from the store.

        This resets the storage to its initial empty state. Primarily
        used by test fixtures to ensure a clean slate between tests.
        """
        self._prompts.clear()
        self._collections.clear()


# Global storage instance
storage = Storage()
