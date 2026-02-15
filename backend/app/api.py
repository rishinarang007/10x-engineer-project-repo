"""FastAPI routes for PromptLab.

This module defines all HTTP endpoints for the PromptLab API, including
CRUD operations for prompts and collections, as well as a health-check
endpoint. CORS is enabled for all origins to allow frontend integration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from app.models import (
    Prompt, PromptCreate, PromptUpdate,
    Collection, CollectionCreate,
    PromptList, CollectionList, HealthResponse,
    get_current_time
)
from app.storage import storage
from app.utils import sort_prompts_by_date, filter_prompts_by_collection, search_prompts
from app import __version__


app = FastAPI(
    title="PromptLab API",
    description=(
        "AI Prompt Engineering Platform\n\n"
        "[Full Documentation](https://rishinarang007.github.io/10x-engineer-project-repo/)"
    ),
    version=__version__,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "docExpansion": "list",
        "filter": True,
        "syntaxHighlight.theme": "monokai",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Health Check ==============


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the current health status and version of the API.

    Returns:
        HealthResponse: A JSON object containing the service status
        (``"healthy"``) and the semantic version string.
    """
    return HealthResponse(status="healthy", version=__version__)


# ============== Prompt Endpoints ==============


@app.get("/prompts", response_model=PromptList)
def list_prompts(
    collection_id: Optional[str] = None,
    search: Optional[str] = None
):
    """List all prompts, with optional filtering and search.

    Retrieves every stored prompt and then optionally narrows the
    result set by collection membership and/or a text search query.
    Results are always sorted by creation date, newest first.

    Args:
        collection_id: If provided, only prompts belonging to this
            collection UUID are returned.
        search: If provided, only prompts whose title or description
            contains this substring (case-insensitive) are returned.

    Returns:
        PromptList: A JSON object with a ``prompts`` array and a
        ``total`` count of matching prompts.
    """
    prompts = storage.get_all_prompts()

    # Filter by collection if specified
    if collection_id:
        prompts = filter_prompts_by_collection(prompts, collection_id)

    # Search if query provided
    if search:
        prompts = search_prompts(prompts, search)

    # Sort by date (newest first)
    prompts = sort_prompts_by_date(prompts, descending=True)

    return PromptList(prompts=prompts, total=len(prompts))


@app.get("/prompts/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: str):
    """Retrieve a single prompt by its unique identifier.

    Args:
        prompt_id: The UUID of the prompt to retrieve.

    Returns:
        Prompt: The full prompt resource including metadata.

    Raises:
        HTTPException: 404 if no prompt with the given ID exists.
    """
    prompt = storage.get_prompt(prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt


@app.post("/prompts", response_model=Prompt, status_code=201)
def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt.

    Validates that the referenced collection (if any) exists, then
    persists the prompt with a server-generated ID and timestamps.

    Args:
        prompt_data: The request body containing ``title``, ``content``,
            and optionally ``description`` and ``collection_id``.

    Returns:
        Prompt: The newly created prompt resource with generated ``id``,
        ``created_at``, and ``updated_at`` fields.

    Raises:
        HTTPException: 400 if ``collection_id`` is provided but does
            not match any existing collection.
    """
    # Validate collection exists if provided
    if prompt_data.collection_id:
        collection = storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    prompt = Prompt(**prompt_data.model_dump())
    return storage.create_prompt(prompt)


@app.put("/prompts/{prompt_id}", response_model=Prompt)
def update_prompt(prompt_id: str, prompt_data: PromptUpdate):
    """Fully replace an existing prompt.

    All mutable fields are overwritten with the values from the request
    body. The ``updated_at`` timestamp is refreshed automatically.
    The original ``id`` and ``created_at`` are preserved.

    Args:
        prompt_id: The UUID of the prompt to update.
        prompt_data: The request body with new values for ``title``,
            ``content``, ``description``, and ``collection_id``.

    Returns:
        Prompt: The updated prompt resource.

    Raises:
        HTTPException: 404 if no prompt with the given ID exists.
        HTTPException: 400 if ``collection_id`` is provided but does
            not match any existing collection.
    """
    existing = storage.get_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Validate collection if provided
    if prompt_data.collection_id:
        collection = storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    updated_prompt = Prompt(
        id=existing.id,
        title=prompt_data.title,
        content=prompt_data.content,
        description=prompt_data.description,
        collection_id=prompt_data.collection_id,
        created_at=existing.created_at,
        updated_at=get_current_time()
    )

    return storage.update_prompt(prompt_id, updated_prompt)


@app.patch("/prompts/{prompt_id}", response_model=Prompt)
def patch_prompt(prompt_id: str, prompt_data: PromptUpdate):
    """Partially update an existing prompt.

    Only the fields explicitly included in the request body are
    modified; all other fields remain unchanged. The ``updated_at``
    timestamp is refreshed whenever at least one field is changed.

    Args:
        prompt_id: The UUID of the prompt to patch.
        prompt_data: The request body containing only the fields to
            update. Omitted fields are left as-is.

    Returns:
        Prompt: The patched prompt resource. If the request body is
        empty (no fields provided), the existing prompt is returned
        unchanged.

    Raises:
        HTTPException: 404 if no prompt with the given ID exists.
        HTTPException: 400 if ``collection_id`` is provided but does
            not match any existing collection.
    """
    existing = storage.get_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Get only the fields that were explicitly provided (exclude_unset=True)
    # This ensures we only update fields that were in the request body
    update_data = prompt_data.model_dump(exclude_unset=True)

    # If no fields were provided, return existing prompt unchanged
    if not update_data:
        return existing

    # Validate collection if provided (and not None)
    if "collection_id" in update_data and update_data["collection_id"] is not None:
        collection = storage.get_collection(update_data["collection_id"])
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    # Create updated prompt with only provided fields
    # Fields not in update_data will remain unchanged from existing prompt
    updated_prompt = existing.model_copy(update=update_data)
    # Always update the timestamp when any field is modified
    updated_prompt.updated_at = get_current_time()

    return storage.update_prompt(prompt_id, updated_prompt)


@app.delete("/prompts/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: str):
    """Delete a prompt by its unique identifier.

    Args:
        prompt_id: The UUID of the prompt to delete.

    Returns:
        None: An empty response with HTTP 204 No Content on success.

    Raises:
        HTTPException: 404 if no prompt with the given ID exists.
    """
    if not storage.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return None


# ============== Collection Endpoints ==============


@app.get("/collections", response_model=CollectionList)
def list_collections():
    """List all collections.

    Returns:
        CollectionList: A JSON object with a ``collections`` array and
        a ``total`` count.
    """
    collections = storage.get_all_collections()
    return CollectionList(collections=collections, total=len(collections))


@app.get("/collections/{collection_id}", response_model=Collection)
def get_collection(collection_id: str):
    """Retrieve a single collection by its unique identifier.

    Args:
        collection_id: The UUID of the collection to retrieve.

    Returns:
        Collection: The full collection resource.

    Raises:
        HTTPException: 404 if no collection with the given ID exists.
    """
    collection = storage.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@app.post("/collections", response_model=Collection, status_code=201)
def create_collection(collection_data: CollectionCreate):
    """Create a new collection.

    Args:
        collection_data: The request body containing ``name`` and
            optionally ``description``.

    Returns:
        Collection: The newly created collection resource with a
        generated ``id`` and ``created_at`` timestamp.
    """
    collection = Collection(**collection_data.model_dump())
    return storage.create_collection(collection)


@app.delete("/collections/{collection_id}", status_code=204)
def delete_collection(collection_id: str):
    """Delete a collection and all of its associated prompts.

    First removes every prompt that belongs to the collection (to
    prevent orphaned references), then deletes the collection itself.

    Args:
        collection_id: The UUID of the collection to delete.

    Returns:
        None: An empty response with HTTP 204 No Content on success.

    Raises:
        HTTPException: 404 if no collection with the given ID exists.
    """
    # Check if collection exists first
    if not storage.get_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    # Delete all prompts that belong to this collection to prevent orphaned references
    prompts_to_delete = storage.get_prompts_by_collection(collection_id)
    for prompt in prompts_to_delete:
        storage.delete_prompt(prompt.id)

    # Now delete the collection
    storage.delete_collection(collection_id)

    return None
