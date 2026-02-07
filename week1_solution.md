# Week 1 Solution - Bug Fixes Documentation

This document provides a detailed explanation of all the bugs that were identified and fixed in the PromptLab API.

## Overview

Four critical bugs were identified and fixed across the codebase:
1. **Bug #1**: `get_prompt` endpoint returning 500 error instead of 404 for non-existent prompts
2. **Bug #2**: `update_prompt` endpoint not updating the `updated_at` timestamp
3. **Bug #3**: `sort_prompts_by_date` function ignoring the `descending` parameter
4. **Bug #4**: `delete_collection` endpoint creating orphaned prompts

All bugs have been fixed and verified with comprehensive test coverage (13/13 tests passing).

---

## Bug #1: Incorrect Error Handling in `get_prompt` Endpoint

### Location
`backend/app/api.py` - Lines 65-73

### Problem
The `get_prompt` function was attempting to access the `id` attribute on a `None` object when a prompt didn't exist, causing a 500 Internal Server Error instead of the expected 404 Not Found response.

### Original Code
```python
@app.get("/prompts/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: str):
    prompt = storage.get_prompt(prompt_id)
    
    # This line causes the bug - accessing attribute on None
    if prompt.id:
        return prompt
```

### Issue
- When `storage.get_prompt(prompt_id)` returns `None` (prompt doesn't exist), accessing `prompt.id` raises an `AttributeError`
- This results in a 500 Internal Server Error instead of a proper 404 Not Found response
- Poor error handling violates REST API best practices

### Solution
Added a null check before accessing the prompt's attributes:

```python
@app.get("/prompts/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: str):
    prompt = storage.get_prompt(prompt_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return prompt
```

### Why This Works
- The `if not prompt:` check properly handles the `None` case before accessing any attributes
- Raises an `HTTPException` with status code 404, which is the correct HTTP response for a resource that doesn't exist
- Follows the same pattern used in other endpoints like `get_collection` and `update_prompt`
- Provides clear error messaging to API consumers

### Impact
- ✅ `test_get_prompt_not_found` now passes
- ✅ `test_delete_prompt` now passes (it verifies deletion by checking for 404)
- ✅ Proper HTTP status codes improve API usability and debugging

---

## Bug #2: Missing Timestamp Update in `update_prompt` Endpoint

### Location
`backend/app/api.py` - Lines 88-111

### Problem
When updating a prompt, the `updated_at` timestamp was not being refreshed, causing it to retain the original creation timestamp instead of reflecting when the prompt was last modified.

### Original Code
```python
updated_prompt = Prompt(
    id=existing.id,
    title=prompt_data.title,
    content=prompt_data.content,
    description=prompt_data.description,
    collection_id=prompt_data.collection_id,
    created_at=existing.created_at,
    updated_at=existing.updated_at  # BUG: Should be get_current_time()
)
```

### Issue
- The `updated_at` field was being copied from the existing prompt instead of being set to the current time
- This defeats the purpose of having an `updated_at` timestamp
- Makes it impossible to track when prompts were last modified
- Could cause confusion when sorting or filtering by modification date

### Solution
Changed `updated_at` to use `get_current_time()`:

```python
updated_prompt = Prompt(
    id=existing.id,
    title=prompt_data.title,
    content=prompt_data.content,
    description=prompt_data.description,
    collection_id=prompt_data.collection_id,
    created_at=existing.created_at,
    updated_at=get_current_time()
)
```

### Why This Works
- `get_current_time()` is already imported from `app.models` at the top of the file
- It provides the current timestamp in the correct format
- Ensures `updated_at` accurately reflects when the prompt was last modified
- Maintains data integrity and enables proper tracking of prompt modifications

### Impact
- ✅ `test_update_prompt` continues to pass
- ✅ Timestamps now accurately reflect modification times
- ✅ Enables future features like "recently updated" prompts

---

## Bug #3: Sorting Function Ignoring `descending` Parameter

### Location
`backend/app/utils.py` - Lines 7-14

### Problem
The `sort_prompts_by_date` function had a `descending` parameter that was completely ignored, always sorting in ascending order (oldest first) regardless of the parameter value.

### Original Code
```python
def sort_prompts_by_date(prompts: List[Prompt], descending: bool = True) -> List[Prompt]:
    """Sort prompts by creation date.
    
    Note: There might be a bug here. Check the sort order!
    """
    # BUG #3: This sorts ascending (oldest first) when it should sort descending (newest first)
    # The 'descending' parameter is ignored!
    return sorted(prompts, key=lambda p: p.created_at)
```

### Issue
- The `descending` parameter was defined but never used
- The function always sorted in ascending order (oldest first)
- When `descending=True` was passed (the default), users expected newest first but got oldest first
- This caused incorrect ordering in the API responses

### Solution
Added the `reverse` parameter to the `sorted()` function call:

```python
def sort_prompts_by_date(prompts: List[Prompt], descending: bool = True) -> List[Prompt]:
    """Sort prompts by creation date.
    
    Args:
        prompts: List of prompts to sort
        descending: If True, sort newest first (descending order). If False, sort oldest first (ascending order).
    """
    return sorted(prompts, key=lambda p: p.created_at, reverse=descending)
```

### Why This Works
- The `reverse` parameter in Python's `sorted()` function controls sort order
- When `reverse=True`, it sorts in descending order (newest first)
- When `reverse=False`, it sorts in ascending order (oldest first)
- By setting `reverse=descending`, the function now correctly respects the parameter
- The default value `descending=True` now correctly sorts newest first

### Impact
- ✅ `test_sorting_order` now passes
- ✅ Prompts are correctly sorted newest first in API responses
- ✅ The function now behaves as documented and expected

---

## Bug #4: Orphaned Prompts When Deleting Collections

### Location
`backend/app/api.py` - Lines 155-169

### Problem
When deleting a collection, all prompts that belonged to that collection were left with an invalid `collection_id` reference, creating orphaned prompts with broken relationships.

### Original Code
```python
@app.delete("/collections/{collection_id}", status_code=204)
def delete_collection(collection_id: str):
    # BUG #4: We delete the collection but don't handle the prompts!
    # Prompts with this collection_id become orphaned with invalid reference
    # Should either: delete the prompts, set collection_id to None, or prevent deletion
    
    if not storage.delete_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Missing: Handle prompts that belong to this collection!
    
    return None
```

### Issue
- Deleting a collection left all associated prompts with a `collection_id` pointing to a non-existent collection
- This created data integrity issues
- Prompts became orphaned and unusable
- Could cause errors when trying to filter or display prompts by collection

### Solution
Delete all prompts belonging to the collection before deleting the collection:

```python
@app.delete("/collections/{collection_id}", status_code=204)
def delete_collection(collection_id: str):
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
```

### Why This Works
- `storage.get_prompts_by_collection(collection_id)` retrieves all prompts with the given `collection_id`
- We iterate through these prompts and delete each one using `storage.delete_prompt()`
- Only after all prompts are deleted do we delete the collection itself
- This maintains referential integrity and prevents orphaned records
- The order of operations is important: check existence → delete children → delete parent

### Alternative Approaches Considered
1. **Set `collection_id` to `None`**: Would preserve prompts but change their meaning
2. **Prevent deletion**: Would require validation but might be too restrictive
3. **Cascade delete** (chosen): Cleanest approach that maintains data integrity

### Impact
- ✅ `test_delete_collection_with_prompts` now passes
- ✅ No orphaned prompts remain after collection deletion
- ✅ Data integrity is maintained
- ✅ Prevents potential errors from invalid references

---

## Test Results

All fixes have been verified with comprehensive test coverage:

```
======================== 13 passed, 2 warnings in 0.34s ========================
```

### Test Breakdown
- ✅ Health check (1 test)
- ✅ Prompt operations (8 tests)
  - Create prompt
  - List prompts (empty and with data)
  - Get prompt (success and not found)
  - Delete prompt
  - Update prompt
  - Sorting order
- ✅ Collection operations (4 tests)
  - Create collection
  - List collections
  - Get collection (not found)
  - Delete collection with prompts

---

## Summary

All four bugs have been successfully identified and fixed:

1. **Bug #1**: Fixed error handling to return proper 404 status codes
2. **Bug #2**: Fixed timestamp tracking to update `updated_at` on modifications
3. **Bug #3**: Fixed sorting function to respect the `descending` parameter
4. **Bug #4**: Fixed collection deletion to prevent orphaned prompts

The codebase now follows best practices for:
- Error handling and HTTP status codes
- Data integrity and referential consistency
- Function parameter usage and documentation
- Timestamp tracking and audit trails

All tests pass, and the API is production-ready.
