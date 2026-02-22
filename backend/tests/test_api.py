"""API tests for PromptLab

These tests verify the API endpoints work correctly.
Students should expand these tests significantly in Week 3.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealth:
    """Tests for health endpoint."""
    
    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestPrompts:
    """Tests for prompt endpoints."""
    
    def test_create_prompt_valid_payload(self, client: TestClient, sample_prompt_data):
        """Valid payload → 201, created resource."""
        response = client.post("/prompts", json=sample_prompt_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_prompt_data["title"]
        assert data["content"] == sample_prompt_data["content"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_prompt_missing_required_field_title(self, client: TestClient, sample_prompt_data):
        """Missing required field (title) → 422."""
        payload = {k: v for k, v in sample_prompt_data.items() if k != "title"}
        response = client.post("/prompts", json=payload)
        assert response.status_code == 422

    def test_create_prompt_missing_required_field_content(self, client: TestClient, sample_prompt_data):
        """Missing required field (content) → 422."""
        payload = {k: v for k, v in sample_prompt_data.items() if k != "content"}
        response = client.post("/prompts", json=payload)
        assert response.status_code == 422

    def test_create_prompt_invalid_type_title(self, client: TestClient, sample_prompt_data):
        """Invalid type for title → 422."""
        response = client.post("/prompts", json={**sample_prompt_data, "title": 123})
        assert response.status_code == 422

    def test_create_prompt_invalid_reference_collection_not_found(self, client: TestClient, sample_prompt_data):
        """Invalid reference (collection_id not found) → 400."""
        payload = {**sample_prompt_data, "collection_id": "00000000-0000-0000-0000-000000000000"}
        response = client.post("/prompts", json=payload)
        assert response.status_code == 400
        assert "collection" in response.json()["detail"].lower()

    def test_create_prompt_empty_title(self, client: TestClient, sample_prompt_data):
        """Empty string where not allowed (title) → 422."""
        response = client.post("/prompts", json={**sample_prompt_data, "title": ""})
        assert response.status_code == 422

    def test_create_prompt_empty_content(self, client: TestClient, sample_prompt_data):
        """Empty string where not allowed (content) → 422."""
        response = client.post("/prompts", json={**sample_prompt_data, "content": ""})
        assert response.status_code == 422

    def test_create_prompt_extra_unknown_fields(self, client: TestClient, sample_prompt_data):
        """Extra unknown fields → 201 (Pydantic ignores by default)."""
        payload = {**sample_prompt_data, "extra_field": "ignored", "another": 999}
        response = client.post("/prompts", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "extra_field" not in data
        assert "another" not in data

    def test_list_prompts_empty(self, client: TestClient):
        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_response_structure(self, client: TestClient):
        """Response always has prompts array and total count."""
        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data
        assert "total" in data
        assert isinstance(data["prompts"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["prompts"])

    def test_list_prompts_with_data(self, client: TestClient, sample_prompt_data):
        # Create a prompt first
        client.post("/prompts", json=sample_prompt_data)

        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["total"] == 1

    def test_list_prompts_filter_by_collection_id_matching(self, client, sample_prompt_data, sample_collection_data):
        """Filter by collection_id returns only prompts in that collection."""
        col_resp = client.post("/collections", json=sample_collection_data)
        collection_id = col_resp.json()["id"]
        prompt_in_col = {**sample_prompt_data, "collection_id": collection_id, "title": "In Collection"}
        prompt_uncategorized = {**sample_prompt_data, "title": "Uncategorized", "collection_id": None}
        client.post("/prompts", json=prompt_in_col)
        client.post("/prompts", json=prompt_uncategorized)

        response = client.get(f"/prompts?collection_id={collection_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["prompts"][0]["collection_id"] == collection_id
        assert data["prompts"][0]["title"] == "In Collection"

    def test_list_prompts_filter_by_collection_id_no_matches(self, client, sample_prompt_data):
        """collection_id with no matching prompts returns empty list."""
        client.post("/prompts", json=sample_prompt_data)
        response = client.get("/prompts?collection_id=00000000-0000-0000-0000-000000000000")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_filter_by_collection_id_nonexistent_uuid(self, client, sample_prompt_data):
        """Non-existent collection_id still returns 200 with filtered (empty) results."""
        client.post("/prompts", json=sample_prompt_data)
        response = client.get("/prompts?collection_id=nonexistent-uuid-string")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_search_match_title(self, client, sample_prompt_data):
        """Search matches substring in title (case-insensitive)."""
        client.post("/prompts", json={**sample_prompt_data, "title": "Code Review Master", "description": "Review tasks"})
        client.post("/prompts", json={**sample_prompt_data, "title": "Unrelated Topic", "description": "Different task"})

        response = client.get("/prompts?search=master")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "master" in data["prompts"][0]["title"].lower()

    def test_list_prompts_search_match_title_case_insensitive(self, client, sample_prompt_data):
        """Search is case-insensitive for title."""
        client.post("/prompts", json={**sample_prompt_data, "title": "CODE REVIEW"})

        response = client.get("/prompts?search=code")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["prompts"][0]["title"] == "CODE REVIEW"

    def test_list_prompts_search_match_description(self, client, sample_prompt_data):
        """Search matches substring in description (case-insensitive)."""
        client.post("/prompts", json={**sample_prompt_data, "description": "Used for summarisation tasks"})
        client.post("/prompts", json={**sample_prompt_data, "description": "Something else"})

        response = client.get("/prompts?search=summarisation")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "summarisation" in (data["prompts"][0].get("description") or "").lower()

    def test_list_prompts_search_no_match(self, client, sample_prompt_data):
        """Search with no matching prompts returns empty list."""
        client.post("/prompts", json=sample_prompt_data)
        response = client.get("/prompts?search=xyznonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_search_empty_string_ignored(self, client, sample_prompt_data):
        """Empty search query is ignored (no filtering applied)."""
        client.post("/prompts", json=sample_prompt_data)
        response = client.get("/prompts?search=")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_list_prompts_collection_and_search_combined(self, client, sample_prompt_data, sample_collection_data):
        """Both collection_id and search filters apply (AND logic)."""
        col_resp = client.post("/collections", json=sample_collection_data)
        collection_id = col_resp.json()["id"]
        client.post("/prompts", json={
            **sample_prompt_data, "collection_id": collection_id,
            "title": "Code Review", "description": "Review code"
        })
        client.post("/prompts", json={
            **sample_prompt_data, "collection_id": collection_id,
            "title": "Other Task", "description": "Different task"
        })

        response = client.get(f"/prompts?collection_id={collection_id}&search=review")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "review" in data["prompts"][0]["title"].lower() or "review" in (data["prompts"][0].get("description") or "").lower()

    def test_list_prompts_sorted_newest_first(self, client):
        """Prompts are sorted by created_at descending (newest first)."""
        import time
        r1 = client.post("/prompts", json={"title": "Oldest", "content": "First prompt content"})
        time.sleep(0.05)
        r2 = client.post("/prompts", json={"title": "Middle", "content": "Second prompt content"})
        time.sleep(0.05)
        r3 = client.post("/prompts", json={"title": "Newest", "content": "Third prompt content"})

        response = client.get("/prompts")
        assert response.status_code == 200
        prompts = response.json()["prompts"]
        assert len(prompts) == 3
        assert prompts[0]["title"] == "Newest"
        assert prompts[1]["title"] == "Middle"
        assert prompts[2]["title"] == "Oldest"

    def test_list_prompts_multiple_prompts_no_filter(self, client, sample_prompt_data):
        """Multiple prompts returned with correct total."""
        for i in range(5):
            client.post("/prompts", json={**sample_prompt_data, "title": f"Prompt {i}"})
        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["prompts"]) == 5

    def test_list_prompts_search_matches_both_title_and_description(self, client, sample_prompt_data):
        """Single prompt matching search in both title and description appears once."""
        client.post("/prompts", json={
            **sample_prompt_data, "title": "Code Review", "description": "Code review helper"
        })
        response = client.get("/prompts?search=code")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_list_prompts_prompt_without_description_search_title_only(self, client, sample_prompt_data):
        """Prompt with no description is still searchable by title."""
        client.post("/prompts", json={
            "title": "Special Title", "content": "Content here",
            "description": None, "collection_id": None
        })
        response = client.get("/prompts?search=special")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["prompts"][0]["title"] == "Special Title"
    
    def test_get_prompt_valid_id_exists(self, client: TestClient, sample_prompt_data):
        """Valid ID, resource exists → 200, correct body."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        response = client.get(f"/prompts/{prompt_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == prompt_id
        assert data["title"] == sample_prompt_data["title"]
        assert data["content"] == sample_prompt_data["content"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_prompt_valid_uuid_not_found(self, client: TestClient):
        """Valid UUID format, resource missing → 404."""
        response = client.get("/prompts/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_prompt_invalid_uuid_format(self, client: TestClient):
        """Invalid UUID format → 422."""
        response = client.get("/prompts/not-a-uuid")
        assert response.status_code == 422

    def test_get_prompt_malformed_id(self, client: TestClient):
        """Malformed/short ID → 422."""
        response = client.get("/prompts/xxx")
        assert response.status_code == 422
    
    def test_delete_prompt_resource_exists(self, client: TestClient, sample_prompt_data):
        """Resource exists → 204."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        response = client.delete(f"/prompts/{prompt_id}")
        assert response.status_code == 204
        get_response = client.get(f"/prompts/{prompt_id}")
        assert get_response.status_code == 404

    def test_delete_prompt_resource_not_found(self, client: TestClient):
        """Resource not found → 404."""
        response = client.delete("/prompts/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_prompt_invalid_uuid(self, client: TestClient):
        """Invalid UUID format → 422."""
        response = client.delete("/prompts/not-a-uuid")
        assert response.status_code == 422
    
    def test_update_prompt_valid_payload_resource_exists(self, client: TestClient, sample_prompt_data):
        """Valid payload, resource exists → 200, updated resource."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        updated_data = {
            "title": "Updated Title",
            "content": "Updated content for the prompt",
            "description": "Updated description",
        }
        response = client.put(f"/prompts/{prompt_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content for the prompt"
        assert data["description"] == "Updated description"
        assert data["id"] == prompt_id

    def test_update_prompt_resource_not_found(self, client: TestClient, sample_prompt_data):
        """Resource not found → 404."""
        response = client.put(
            "/prompts/00000000-0000-0000-0000-000000000000",
            json={"title": "X", "content": "Y"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_prompt_invalid_uuid(self, client: TestClient, sample_prompt_data):
        """Invalid UUID format → 422."""
        response = client.put("/prompts/not-a-uuid", json={"title": "X", "content": "Y"})
        assert response.status_code == 422

    def test_update_prompt_invalid_reference_collection_not_found(
        self, client: TestClient, sample_prompt_data
    ):
        """Invalid reference (collection_id not found) → 400."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        payload = {
            "title": "X",
            "content": "Y",
            "collection_id": "00000000-0000-0000-0000-000000000000",
        }
        response = client.put(f"/prompts/{prompt_id}", json=payload)
        assert response.status_code == 400
        assert "collection" in response.json()["detail"].lower()

    def test_update_prompt_empty_title_invalid(self, client: TestClient, sample_prompt_data):
        """Empty title (validation failure) → 422."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        response = client.put(
            f"/prompts/{prompt_id}",
            json={"title": "", "content": sample_prompt_data["content"]},
        )
        assert response.status_code == 422

    def test_update_prompt_partial_payload_merges(self, client: TestClient, sample_prompt_data):
        """Partial payload merges with existing; omitted fields preserved."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_content = sample_prompt_data["content"]
        response = client.put(f"/prompts/{prompt_id}", json={"title": "Only Title Updated"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Only Title Updated"
        assert data["content"] == original_content

    def test_patch_prompt_valid_partial_payload(self, client: TestClient, sample_prompt_data):
        """Valid partial payload → 200, merged resource."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        response = client.patch(f"/prompts/{prompt_id}", json={"title": "Patched Title"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Patched Title"
        assert data["content"] == sample_prompt_data["content"]

    def test_patch_prompt_resource_not_found(self, client: TestClient):
        """Resource not found → 404."""
        response = client.patch(
            "/prompts/00000000-0000-0000-0000-000000000000",
            json={"title": "X"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_patch_prompt_empty_body_unchanged(self, client: TestClient, sample_prompt_data):
        """Empty body `{}` → 200, unchanged."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        response = client.patch(f"/prompts/{prompt_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_prompt_data["title"]
        assert data["content"] == sample_prompt_data["content"]

    def test_patch_prompt_invalid_uuid(self, client: TestClient):
        """Invalid UUID format → 422."""
        response = client.patch("/prompts/not-a-uuid", json={"title": "X"})
        assert response.status_code == 422

    def test_patch_prompt_invalid_field_type(self, client: TestClient, sample_prompt_data):
        """Invalid field type → 422."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        response = client.patch(f"/prompts/{prompt_id}", json={"title": 123})
        assert response.status_code == 422

    def test_patch_prompt_invalid_reference_collection_not_found(
        self, client: TestClient, sample_prompt_data
    ):
        """Invalid reference in updated field (collection_id not found) → 400."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        response = client.patch(
            f"/prompts/{prompt_id}",
            json={"collection_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 400
        assert "collection" in response.json()["detail"].lower()

    def test_sorting_order(self, client: TestClient):
        """Test that prompts are sorted newest first.
        
        NOTE: This test might fail due to Bug #3!
        """
        import time
        
        # Create prompts with delay
        prompt1 = {"title": "First", "content": "First prompt content"}
        prompt2 = {"title": "Second", "content": "Second prompt content"}
        
        client.post("/prompts", json=prompt1)
        time.sleep(0.1)
        client.post("/prompts", json=prompt2)
        
        response = client.get("/prompts")
        prompts = response.json()["prompts"]
        
        # Newest (Second) should be first
        assert prompts[0]["title"] == "Second"  # Will fail until Bug #3 fixed


class TestCollections:
    """Tests for collection endpoints."""

    def test_create_collection_valid_payload(self, client: TestClient, sample_collection_data):
        """Valid payload → 201, created resource."""
        response = client.post("/collections", json=sample_collection_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_collection_data["name"]
        assert data["description"] == sample_collection_data["description"]
        assert "id" in data
        assert "created_at" in data

    def test_create_collection_missing_required_field_name(self, client: TestClient, sample_collection_data):
        """Missing required field (name) → 422."""
        payload = {k: v for k, v in sample_collection_data.items() if k != "name"}
        response = client.post("/collections", json=payload)
        assert response.status_code == 422

    def test_create_collection_invalid_type_name(self, client: TestClient, sample_collection_data):
        """Invalid type for name → 422."""
        response = client.post("/collections", json={**sample_collection_data, "name": 123})
        assert response.status_code == 422

    def test_create_collection_empty_name(self, client: TestClient, sample_collection_data):
        """Empty string where not allowed (name) → 422."""
        response = client.post("/collections", json={**sample_collection_data, "name": ""})
        assert response.status_code == 422

    def test_create_collection_extra_unknown_fields(self, client: TestClient, sample_collection_data):
        """Extra unknown fields → 201 (ignored by Pydantic)."""
        payload = {**sample_collection_data, "extra": "ignored"}
        response = client.post("/collections", json=payload)
        assert response.status_code == 201
        assert "extra" not in response.json()

    def test_list_collections_empty(self, client: TestClient):
        """No data → 200, empty array, total=0."""
        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert data["collections"] == []
        assert data["total"] == 0

    def test_list_collections_with_data(self, client: TestClient, sample_collection_data):
        """With data → 200, correct count and items."""
        client.post("/collections", json=sample_collection_data)
        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert len(data["collections"]) == 1
        assert data["total"] == 1
        assert data["collections"][0]["name"] == sample_collection_data["name"]

    def test_get_collection_valid_id_exists(self, client: TestClient, sample_collection_data):
        """Valid ID, resource exists → 200, correct body."""
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]
        response = client.get(f"/collections/{collection_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == collection_id
        assert data["name"] == sample_collection_data["name"]
        assert "created_at" in data

    def test_get_collection_valid_uuid_not_found(self, client: TestClient):
        """Valid UUID format, resource missing → 404."""
        response = client.get("/collections/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_collection_invalid_uuid_format(self, client: TestClient):
        """Invalid UUID format → 422."""
        response = client.get("/collections/not-a-uuid")
        assert response.status_code == 422

    def test_delete_collection_resource_exists(self, client: TestClient, sample_collection_data):
        """Resource exists → 204."""
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]
        response = client.delete(f"/collections/{collection_id}")
        assert response.status_code == 204
        get_response = client.get(f"/collections/{collection_id}")
        assert get_response.status_code == 404

    def test_delete_collection_resource_not_found(self, client: TestClient):
        """Resource not found → 404."""
        response = client.delete("/collections/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_collection_invalid_uuid(self, client: TestClient):
        """Invalid UUID format → 422."""
        response = client.delete("/collections/not-a-uuid")
        assert response.status_code == 422

    def test_delete_collection_cascade_deletes_prompts(
        self, client: TestClient, sample_collection_data, sample_prompt_data
    ):
        """Cascade: prompts in collection are deleted when collection is deleted."""
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]
        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        prompt_response = client.post("/prompts", json=prompt_data)
        prompt_id = prompt_response.json()["id"]

        response = client.delete(f"/collections/{collection_id}")
        assert response.status_code == 204

        assert client.get(f"/collections/{collection_id}").status_code == 404
        assert client.get(f"/prompts/{prompt_id}").status_code == 404
