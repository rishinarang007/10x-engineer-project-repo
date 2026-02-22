"""FastAPI routes for PromptLab.

This module defines all HTTP endpoints for the PromptLab API, including
CRUD operations for prompts and collections, as well as a health-check
endpoint. CORS is enabled for all origins to allow frontend integration.
"""

from uuid import UUID
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

import re
from app.models import (
    Prompt, PromptCreate, PromptUpdate,
    Collection, CollectionCreate,
    Tag, TagCreate, TagList, TagWithCount, TagAssignment,
    PromptList, CollectionList, HealthResponse,
    get_current_time
)
from app.storage import storage
from app.utils import (
    sort_prompts_by_date,
    filter_prompts_by_collection,
    filter_prompts_by_tags,
    search_prompts,
)
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

TAG_NAME_PATTERN = re.compile(r"^[a-z0-9_-]+$")


def _normalise_tag_name(name: str) -> str:
    """Trim and lowercase tag name."""
    return name.strip().lower()


def _enrich_prompt_with_tags(prompt: Prompt) -> Prompt:
    """Add tags to a prompt for response."""
    tags = storage.get_tags_for_prompt(prompt.id)
    return prompt.model_copy(update={"tags": tags})


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
    search: Optional[str] = None,
    tags: Optional[str] = None,
    tag_match: str = "all",
):
    """List all prompts, with optional filtering and search.

    Retrieves every stored prompt and then optionally narrows the
    result set by collection membership, tags, and/or a text search query.
    Results are always sorted by creation date, newest first.

    Args:
        collection_id: If provided, only prompts belonging to this
            collection UUID are returned.
        search: If provided, only prompts whose title or description
            contains this substring (case-insensitive) are returned.
        tags: Comma-separated tag names (e.g. gpt-4,code-review).
        tag_match: "all" = prompt must have every tag; "any" = at least one.

    Returns:
        PromptList: A JSON object with a ``prompts`` array and a
        ``total`` count of matching prompts.
    """
    prompts = storage.get_all_prompts()

    # Filter by collection if specified
    if collection_id:
        prompts = filter_prompts_by_collection(prompts, collection_id)

    # Enrich with tags before tag filtering (filter needs tags on each prompt)
    prompts = [_enrich_prompt_with_tags(p) for p in prompts]

    # Filter by tags if specified (E-9: empty tags param ignored)
    if tags and tags.strip():
        tag_names = [t.strip().lower() for t in tags.split(",") if t.strip()]
        if tag_names:
            prompts = filter_prompts_by_tags(prompts, tag_names, match=tag_match)

    # Search if query provided
    if search:
        prompts = search_prompts(prompts, search)

    # Sort by date (newest first)
    prompts = sort_prompts_by_date(prompts, descending=True)

    return PromptList(prompts=prompts, total=len(prompts))


@app.get("/prompts/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: UUID):
    """Retrieve a single prompt by its unique identifier.

    Args:
        prompt_id: The UUID of the prompt to retrieve.

    Returns:
        Prompt: The full prompt resource including metadata.

    Raises:
        HTTPException: 404 if no prompt with the given ID exists.
    """
    prompt = storage.get_prompt(str(prompt_id))

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return _enrich_prompt_with_tags(prompt)


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

    # Validate tag_ids if provided
    tag_ids = getattr(prompt_data, "tag_ids", None) or []
    if tag_ids:
        invalid = [tid for tid in tag_ids if not storage.get_tag(tid)]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Tags not found: {', '.join(invalid)}",
            )

    dump = prompt_data.model_dump(exclude={"tag_ids"})
    prompt = Prompt(**dump)
    storage.create_prompt(prompt)
    if tag_ids:
        storage.attach_tags(prompt.id, set(tag_ids))
    return _enrich_prompt_with_tags(prompt)


@app.put("/prompts/{prompt_id}", response_model=Prompt)
def update_prompt(prompt_id: UUID, prompt_data: PromptUpdate):
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
    existing = storage.get_prompt(str(prompt_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Validate collection if provided
    if prompt_data.collection_id is not None:
        collection = storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    # Merge: use provided values or fall back to existing
    provided = prompt_data.model_dump(exclude_unset=True)
    title = provided.get("title", existing.title)
    content = provided.get("content", existing.content)
    description = provided.get("description", existing.description)
    collection_id = provided.get("collection_id", existing.collection_id)

    # Validate and apply tag_ids if provided (replaces entirely)
    if "tag_ids" in provided:
        tag_ids = provided["tag_ids"] or []
        if tag_ids:
            invalid = [tid for tid in tag_ids if not storage.get_tag(tid)]
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tags not found: {', '.join(invalid)}",
                )
        storage.set_tags(str(prompt_id), set(tag_ids))

    updated_prompt = Prompt(
        id=existing.id,
        title=title,
        content=content,
        description=description,
        collection_id=collection_id,
        created_at=existing.created_at,
        updated_at=get_current_time()
    )

    return _enrich_prompt_with_tags(storage.update_prompt(str(prompt_id), updated_prompt))


@app.patch("/prompts/{prompt_id}", response_model=Prompt)
def patch_prompt(prompt_id: UUID, prompt_data: PromptUpdate):
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
    existing = storage.get_prompt(str(prompt_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Get only the fields that were explicitly provided (exclude_unset=True)
    # This ensures we only update fields that were in the request body
    update_data = prompt_data.model_dump(exclude_unset=True)

    # If no fields were provided, return existing prompt unchanged
    if not update_data:
        return _enrich_prompt_with_tags(existing)

    # Validate collection if provided (and not None)
    if "collection_id" in update_data and update_data["collection_id"] is not None:
        collection = storage.get_collection(update_data["collection_id"])
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    # Apply tag_ids if provided (replaces entirely)
    if "tag_ids" in update_data:
        tag_ids = update_data.pop("tag_ids") or []
        if tag_ids:
            invalid = [tid for tid in tag_ids if not storage.get_tag(tid)]
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tags not found: {', '.join(invalid)}",
                )
        storage.set_tags(str(prompt_id), set(tag_ids))

    # Create updated prompt with only provided fields
    updated_prompt = existing.model_copy(update=update_data)
    updated_prompt.updated_at = get_current_time()

    return _enrich_prompt_with_tags(storage.update_prompt(str(prompt_id), updated_prompt))


@app.delete("/prompts/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: UUID):
    """Delete a prompt by its unique identifier.

    Args:
        prompt_id: The UUID of the prompt to delete.

    Returns:
        None: An empty response with HTTP 204 No Content on success.

    Raises:
        HTTPException: 404 if no prompt with the given ID exists.
    """
    if not storage.delete_prompt(str(prompt_id)):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return None


# ============== Tag Endpoints ==============


@app.post("/tags", response_model=Tag, status_code=201)
def create_tag(tag_data: TagCreate):
    """Create a new tag.

    Name is normalised (lowercase, trimmed) before storage.
    Returns 409 if a tag with the same normalised name already exists.

    Args:
        tag_data: Request body with name.

    Returns:
        Tag: The created tag with id, name, created_at.

    Raises:
        HTTPException: 409 if tag name already exists.
        HTTPException: 422 if name fails validation after normalisation.
    """
    normalised = _normalise_tag_name(tag_data.name)
    if not normalised:
        raise HTTPException(
            status_code=422,
            detail="Tag name cannot be empty or whitespace only.",
        )
    if not TAG_NAME_PATTERN.match(normalised):
        raise HTTPException(
            status_code=422,
            detail="Tag name may only contain letters, digits, hyphens, and underscores.",
        )
    if storage.get_tag_by_name(normalised):
        raise HTTPException(
            status_code=409,
            detail=f"Tag '{normalised}' already exists",
        )
    tag = Tag(name=normalised)
    storage.create_tag(tag)
    return tag


@app.get("/tags", response_model=TagList)
def list_tags():
    """List all tags with prompt counts, sorted alphabetically by name."""
    tags = storage.get_all_tags()
    tags_sorted = sorted(tags, key=lambda t: t.name)
    with_count = [
        TagWithCount(
            **t.model_dump(),
            prompt_count=storage.get_prompt_count_for_tag(t.id),
        )
        for t in tags_sorted
    ]
    return TagList(tags=with_count, total=len(with_count))


@app.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: UUID):
    """Delete a tag and detach it from all prompts.

    Raises:
        HTTPException: 404 if tag not found.
    """
    if not storage.get_tag(str(tag_id)):
        raise HTTPException(status_code=404, detail="Tag not found")
    storage.delete_tag(str(tag_id))
    return None


# ============== Prompt-Tag Operations ==============


@app.post("/prompts/{prompt_id}/tags", response_model=Prompt)
def attach_tags_to_prompt(prompt_id: UUID, body: TagAssignment):
    """Attach one or more tags to a prompt.

    Tags already on the prompt are silently ignored.
    Returns 400 if any tag_id does not exist.

    Raises:
        HTTPException: 404 if prompt not found.
        HTTPException: 400 if any tag_id not found.
    """
    existing = storage.get_prompt(str(prompt_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    tag_ids = list(dict.fromkeys(body.tag_ids))  # Deduplicate preserving order
    invalid = [tid for tid in tag_ids if not storage.get_tag(tid)]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Tags not found: {', '.join(invalid)}",
        )
    storage.attach_tags(str(prompt_id), set(tag_ids))
    updated = existing.model_copy(update={"updated_at": get_current_time()})
    storage.update_prompt(str(prompt_id), updated)
    return _enrich_prompt_with_tags(storage.get_prompt(str(prompt_id)))


@app.delete("/prompts/{prompt_id}/tags", response_model=Prompt)
def detach_tags_from_prompt(prompt_id: UUID, body: TagAssignment):
    """Detach one or more tags from a prompt.

    Tags not on the prompt are silently ignored.

    Raises:
        HTTPException: 404 if prompt not found.
    """
    existing = storage.get_prompt(str(prompt_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    storage.detach_tags(str(prompt_id), set(body.tag_ids))
    updated = existing.model_copy(update={"updated_at": get_current_time()})
    storage.update_prompt(str(prompt_id), updated)
    return _enrich_prompt_with_tags(storage.get_prompt(str(prompt_id)))


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
def get_collection(collection_id: UUID):
    """Retrieve a single collection by its unique identifier.

    Args:
        collection_id: The UUID of the collection to retrieve.

    Returns:
        Collection: The full collection resource.

    Raises:
        HTTPException: 404 if no collection with the given ID exists.
    """
    collection = storage.get_collection(str(collection_id))
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
def delete_collection(collection_id: UUID):
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
    cid = str(collection_id)
    if not storage.get_collection(cid):
        raise HTTPException(status_code=404, detail="Collection not found")

    # Delete all prompts that belong to this collection to prevent orphaned references
    prompts_to_delete = storage.get_prompts_by_collection(cid)
    for prompt in prompts_to_delete:
        storage.delete_prompt(prompt.id)

    # Now delete the collection
    storage.delete_collection(cid)

    return None
