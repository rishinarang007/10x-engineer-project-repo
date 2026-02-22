"""TDD tests for Tagging System (specs/tagging-system.md).

These tests define the expected behaviour BEFORE implementation.
All tests will FAIL until the tagging feature is implemented.
Run with: pytest tests/test_tagging.py -v
"""

import pytest
from fastapi.testclient import TestClient


# ============== Tag CRUD ==============


class TestCreateTag:
    """POST /tags - Create a new tag."""

    def test_create_tag_valid_payload(self, client: TestClient):
        """Valid name → 201, created tag with id, name, created_at."""
        response = client.post("/tags", json={"name": "code-review"})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "code-review"
        assert "created_at" in data

    def test_create_tag_name_normalised_lowercase(self, client: TestClient):
        """Name normalised to lowercase before storage (E-1)."""
        response = client.post("/tags", json={"name": "Code-Review"})
        assert response.status_code == 201
        assert response.json()["name"] == "code-review"

    def test_create_tag_name_trimmed(self, client: TestClient):
        """Leading/trailing whitespace trimmed (E-1)."""
        response = client.post("/tags", json={"name": "  code-review  "})
        assert response.status_code == 201
        assert response.json()["name"] == "code-review"

    def test_create_tag_duplicate_name_returns_409(self, client: TestClient):
        """Tag with same normalised name already exists → 409 (E-1)."""
        client.post("/tags", json={"name": "code-review"})
        response = client.post("/tags", json={"name": "code-review"})
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_create_tag_duplicate_name_case_insensitive_returns_409(self, client: TestClient):
        """Duplicate with different case → 409 (normalised same)."""
        client.post("/tags", json={"name": "code-review"})
        response = client.post("/tags", json={"name": "CODE-REVIEW"})
        assert response.status_code == 409

    def test_create_tag_missing_name_returns_422(self, client: TestClient):
        """Missing required field (name) → 422."""
        response = client.post("/tags", json={})
        assert response.status_code == 422

    def test_create_tag_empty_name_returns_422(self, client: TestClient):
        """Empty name → 422."""
        response = client.post("/tags", json={"name": ""})
        assert response.status_code == 422

    def test_create_tag_invalid_characters_returns_422(self, client: TestClient):
        """Invalid chars (space, punctuation) after normalisation → 422 (E-2)."""
        response = client.post("/tags", json={"name": "my tag!"})
        assert response.status_code == 422

    def test_create_tag_exceeds_max_length_returns_422(self, client: TestClient):
        """Name exceeds 50 chars → 422."""
        response = client.post("/tags", json={"name": "a" * 51})
        assert response.status_code == 422

    def test_create_tag_valid_characters_accepted(self, client: TestClient):
        """Valid: letters, digits, hyphens, underscores (^[a-z0-9_-]+$)."""
        response = client.post("/tags", json={"name": "gpt-4_test"})
        assert response.status_code == 201
        assert response.json()["name"] == "gpt-4_test"


class TestListTags:
    """GET /tags - List all tags."""

    def test_list_tags_empty(self, client: TestClient):
        """No tags → 200, empty array, total=0."""
        response = client.get("/tags")
        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == []
        assert data["total"] == 0

    def test_list_tags_with_data(self, client: TestClient):
        """With tags → 200, tags array with prompt_count, total."""
        client.post("/tags", json={"name": "gpt-4"})
        client.post("/tags", json={"name": "code-review"})
        response = client.get("/tags")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["tags"]) == 2
        for tag in data["tags"]:
            assert "id" in tag
            assert "name" in tag
            assert "created_at" in tag
            assert "prompt_count" in tag
            assert isinstance(tag["prompt_count"], int)

    def test_list_tags_sorted_alphabetically(self, client: TestClient):
        """Tags sorted alphabetically by name."""
        client.post("/tags", json={"name": "zebra"})
        client.post("/tags", json={"name": "alpha"})
        client.post("/tags", json={"name": "middle"})
        response = client.get("/tags")
        names = [t["name"] for t in response.json()["tags"]]
        assert names == ["alpha", "middle", "zebra"]


class TestDeleteTag:
    """DELETE /tags/{tag_id} - Delete a tag."""

    def test_delete_tag_exists_returns_204(self, client: TestClient):
        """Tag exists → 204 No Content."""
        create_resp = client.post("/tags", json={"name": "deleteme"})
        tag_id = create_resp.json()["id"]
        response = client.delete(f"/tags/{tag_id}")
        assert response.status_code == 204
        assert client.get(f"/tags").status_code == 200
        tags = [t for t in client.get("/tags").json()["tags"] if t["id"] == tag_id]
        assert len(tags) == 0

    def test_delete_tag_not_found_returns_404(self, client: TestClient):
        """Tag not found → 404."""
        response = client.delete("/tags/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_delete_tag_invalid_uuid_returns_422(self, client: TestClient):
        """Invalid UUID format → 422."""
        response = client.delete("/tags/not-a-uuid")
        assert response.status_code == 422

    def test_delete_tag_cascade_detaches_from_prompts(self, client: TestClient, sample_prompt_data):
        """Tag deleted → detached from all prompts; prompts not deleted (E-6)."""
        tag_resp = client.post("/tags", json={"name": "cascade-test"})
        tag_id = tag_resp.json()["id"]
        prompt_resp = client.post("/prompts", json=sample_prompt_data)
        prompt_id = prompt_resp.json()["id"]
        client.post(f"/prompts/{prompt_id}/tags", json={"tag_ids": [tag_id]})

        response = client.delete(f"/tags/{tag_id}")
        assert response.status_code == 204

        prompt = client.get(f"/prompts/{prompt_id}").json()
        assert prompt["id"] == prompt_id
        tag_names = [t["name"] for t in prompt["tags"]]
        assert "cascade-test" not in tag_names


# ============== Prompt-Tag Attach / Detach ==============


class TestAttachTagsToPrompt:
    """POST /prompts/{prompt_id}/tags - Attach tags to a prompt."""

    def test_attach_tags_valid(self, client: TestClient, sample_prompt_data):
        """Valid tag_ids → 200, prompt returned with tags array."""
        tag1 = client.post("/tags", json={"name": "t1"}).json()
        tag2 = client.post("/tags", json={"name": "t2"}).json()
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        response = client.post(
            f"/prompts/{prompt['id']}/tags",
            json={"tag_ids": [tag1["id"], tag2["id"]]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 2
        assert {t["name"] for t in data["tags"]} == {"t1", "t2"}
        assert "updated_at" in data

    def test_attach_tags_prompt_not_found_returns_404(self, client: TestClient):
        """Prompt not found → 404."""
        tag = client.post("/tags", json={"name": "t1"}).json()
        response = client.post(
            "/prompts/00000000-0000-0000-0000-000000000000/tags",
            json={"tag_ids": [tag["id"]]},
        )
        assert response.status_code == 404

    def test_attach_tags_invalid_tag_id_returns_400(self, client: TestClient, sample_prompt_data):
        """One or more tag_ids do not exist → 400 (E-7)."""
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        response = client.post(
            f"/prompts/{prompt['id']}/tags",
            json={"tag_ids": ["00000000-0000-0000-0000-000000000000"]},
        )
        assert response.status_code == 400
        assert "tag" in response.json()["detail"].lower()

    def test_attach_tags_already_attached_silently_ignored(self, client: TestClient, sample_prompt_data):
        """Tags already on prompt → silently ignored, no error (E-4)."""
        tag = client.post("/tags", json={"name": "existing"}).json()
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        client.post(f"/prompts/{prompt['id']}/tags", json={"tag_ids": [tag["id"]]})
        response = client.post(f"/prompts/{prompt['id']}/tags", json={"tag_ids": [tag["id"]]})
        assert response.status_code == 200
        assert len(response.json()["tags"]) == 1

    def test_attach_tags_duplicate_ids_deduplicated(self, client: TestClient, sample_prompt_data):
        """Duplicate tag_ids in body → deduplicated, attached once (E-3)."""
        tag = client.post("/tags", json={"name": "dup"}).json()
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        response = client.post(
            f"/prompts/{prompt['id']}/tags",
            json={"tag_ids": [tag["id"], tag["id"]]},
        )
        assert response.status_code == 200
        assert len(response.json()["tags"]) == 1

    def test_attach_tags_missing_tag_ids_returns_422(self, client: TestClient, sample_prompt_data):
        """Missing tag_ids or empty array → 422."""
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        response = client.post(f"/prompts/{prompt['id']}/tags", json={})
        assert response.status_code == 422


class TestDetachTagsFromPrompt:
    """DELETE /prompts/{prompt_id}/tags - Detach tags from a prompt."""

    def test_detach_tags_valid(self, client: TestClient, sample_prompt_data):
        """Valid tag_ids → 200, prompt returned without those tags."""
        tag = client.post("/tags", json={"name": "detach-me"}).json()
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        client.post(f"/prompts/{prompt['id']}/tags", json={"tag_ids": [tag["id"]]})
        response = client.delete(
            f"/prompts/{prompt['id']}/tags",
            json={"tag_ids": [tag["id"]]},
        )
        assert response.status_code == 200
        assert len(response.json()["tags"]) == 0

    def test_detach_tags_not_on_prompt_silently_ignored(self, client: TestClient, sample_prompt_data):
        """Tags not on prompt → silently ignored (E-5)."""
        tag1 = client.post("/tags", json={"name": "on-prompt"}).json()
        tag2 = client.post("/tags", json={"name": "not-on-prompt"}).json()
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        client.post(f"/prompts/{prompt['id']}/tags", json={"tag_ids": [tag1["id"]]})
        response = client.delete(
            f"/prompts/{prompt['id']}/tags",
            json={"tag_ids": [tag1["id"], tag2["id"]]},
        )
        assert response.status_code == 200
        assert len(response.json()["tags"]) == 0

    def test_detach_tags_prompt_not_found_returns_404(self, client: TestClient):
        """Prompt not found → 404."""
        tag = client.post("/tags", json={"name": "t1"}).json()
        response = client.delete(
            "/prompts/00000000-0000-0000-0000-000000000000/tags",
            json={"tag_ids": [tag["id"]]},
        )
        assert response.status_code == 404


# ============== Prompt responses include tags ==============


class TestPromptIncludesTags:
    """Prompt response model includes tags field (US-6)."""

    def test_get_prompt_includes_tags(self, client: TestClient, sample_prompt_data):
        """GET /prompts/{id} includes tags array."""
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        response = client.get(f"/prompts/{prompt['id']}")
        assert "tags" in response.json()
        assert response.json()["tags"] == []

    def test_list_prompts_includes_tags(self, client: TestClient, sample_prompt_data):
        """GET /prompts includes tags in each prompt."""
        client.post("/prompts", json=sample_prompt_data)
        response = client.get("/prompts")
        assert response.status_code == 200
        for p in response.json()["prompts"]:
            assert "tags" in p
            assert isinstance(p["tags"], list)

    def test_tags_sorted_alphabetically_on_prompt(self, client: TestClient, sample_prompt_data):
        """Tags on prompt sorted alphabetically by name."""
        t1 = client.post("/tags", json={"name": "zebra"}).json()
        t2 = client.post("/tags", json={"name": "alpha"}).json()
        prompt = client.post("/prompts", json=sample_prompt_data).json()
        client.post(f"/prompts/{prompt['id']}/tags", json={"tag_ids": [t1["id"], t2["id"]]})
        response = client.get(f"/prompts/{prompt['id']}")
        names = [t["name"] for t in response.json()["tags"]]
        assert names == ["alpha", "zebra"]


# ============== Prompt Create/Update with tag_ids ==============


class TestPromptCreateWithTags:
    """POST /prompts with optional tag_ids (US-8)."""

    def test_create_prompt_with_tag_ids(self, client: TestClient, sample_prompt_data):
        """Valid tag_ids → prompt created with tags attached."""
        tag = client.post("/tags", json={"name": "create-with"}).json()
        payload = {**sample_prompt_data, "tag_ids": [tag["id"]]}
        response = client.post("/prompts", json=payload)
        assert response.status_code == 201
        assert len(response.json()["tags"]) == 1
        assert response.json()["tags"][0]["name"] == "create-with"

    def test_create_prompt_invalid_tag_ids_returns_400(self, client: TestClient, sample_prompt_data):
        """Invalid tag_id → 400, no prompt created (E-7)."""
        payload = {
            **sample_prompt_data,
            "tag_ids": ["00000000-0000-0000-0000-000000000000"],
        }
        response = client.post("/prompts", json=payload)
        assert response.status_code == 400

    def test_create_prompt_without_tag_ids_ok(self, client: TestClient, sample_prompt_data):
        """No tag_ids → prompt created with empty tags."""
        response = client.post("/prompts", json=sample_prompt_data)
        assert response.status_code == 201
        assert response.json()["tags"] == []


class TestPromptUpdateWithTags:
    """PUT /prompts/{id} and PATCH /prompts/{id} with tag_ids (US-8)."""

    def test_put_prompt_tag_ids_replaces(self, client: TestClient, sample_prompt_data):
        """PUT with tag_ids → replaces current tag set entirely."""
        t1 = client.post("/tags", json={"name": "old"}).json()
        t2 = client.post("/tags", json={"name": "new"}).json()
        prompt = client.post(
            "/prompts",
            json={**sample_prompt_data, "tag_ids": [t1["id"]]},
        ).json()
        response = client.put(
            f"/prompts/{prompt['id']}",
            json={
                "title": sample_prompt_data["title"],
                "content": sample_prompt_data["content"],
                "tag_ids": [t2["id"]],
            },
        )
        assert response.status_code == 200
        names = [t["name"] for t in response.json()["tags"]]
        assert names == ["new"]

    def test_patch_prompt_tag_ids_replaces_when_provided(self, client: TestClient, sample_prompt_data):
        """PATCH with tag_ids → replaces; without tag_ids → unchanged."""
        t1 = client.post("/tags", json={"name": "initial"}).json()
        prompt = client.post(
            "/prompts",
            json={**sample_prompt_data, "tag_ids": [t1["id"]]},
        ).json()
        client.patch(f"/prompts/{prompt['id']}", json={"title": "Updated"})
        response = client.get(f"/prompts/{prompt['id']}")
        assert len(response.json()["tags"]) == 1
        assert response.json()["tags"][0]["name"] == "initial"


# ============== Filter prompts by tags ==============


class TestFilterPromptsByTags:
    """GET /prompts?tags=... & tag_match=... (US-7)."""

    def test_filter_prompts_by_tags_and_logic(self, client: TestClient, sample_prompt_data):
        """tags param with AND logic (default) → only prompts with ALL tags."""
        t1 = client.post("/tags", json={"name": "gpt-4"}).json()
        t2 = client.post("/tags", json={"name": "code-review"}).json()
        p1 = client.post(
            "/prompts",
            json={**sample_prompt_data, "title": "Both", "tag_ids": [t1["id"], t2["id"]]},
        ).json()
        p2 = client.post(
            "/prompts",
            json={**sample_prompt_data, "title": "One", "tag_ids": [t1["id"]]},
        ).json()
        response = client.get("/prompts?tags=gpt-4,code-review")
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["prompts"][0]["title"] == "Both"

    def test_filter_prompts_by_tags_any_logic(self, client: TestClient, sample_prompt_data):
        """tag_match=any → prompts with at least ONE tag."""
        t1 = client.post("/tags", json={"name": "aaa"}).json()
        t2 = client.post("/tags", json={"name": "bbb"}).json()
        p1 = client.post(
            "/prompts",
            json={**sample_prompt_data, "title": "A only", "tag_ids": [t1["id"]]},
        ).json()
        p2 = client.post(
            "/prompts",
            json={**sample_prompt_data, "title": "B only", "tag_ids": [t2["id"]]},
        ).json()
        response = client.get("/prompts?tags=aaa,bbb&tag_match=any")
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_filter_prompts_nonexistent_tag_returns_empty(self, client: TestClient, sample_prompt_data):
        """Filter by non-existent tag name → empty list, no error (E-8)."""
        client.post("/prompts", json=sample_prompt_data)
        response = client.get("/prompts?tags=nonexistent-tag")
        assert response.status_code == 200
        assert response.json()["prompts"] == []
        assert response.json()["total"] == 0

    def test_filter_prompts_empty_tags_param_ignored(self, client: TestClient, sample_prompt_data):
        """Empty tags param (?tags=) → ignored, return all (E-9)."""
        client.post("/prompts", json=sample_prompt_data)
        response = client.get("/prompts?tags=")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    def test_filter_prompts_tags_combined_with_collection(self, client: TestClient, sample_prompt_data, sample_collection_data):
        """tags filter ANDs with collection_id."""
        col = client.post("/collections", json=sample_collection_data).json()
        tag = client.post("/tags", json={"name": "in-col"}).json()
        p_in = client.post(
            "/prompts",
            json={
                **sample_prompt_data,
                "title": "In",
                "collection_id": col["id"],
                "tag_ids": [tag["id"]],
            },
        ).json()
        p_out = client.post(
            "/prompts",
            json={
                **sample_prompt_data,
                "title": "Out",
                "collection_id": None,
                "tag_ids": [tag["id"]],
            },
        ).json()
        response = client.get(f"/prompts?collection_id={col['id']}&tags=in-col")
        assert response.json()["total"] == 1
        assert response.json()["prompts"][0]["title"] == "In"
