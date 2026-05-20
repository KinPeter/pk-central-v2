# Testing Guidelines

## Unit tests

- **Location:** `unit_tests/` — mirrors `app/` structure exactly. Every module in `app/modules/<name>/` has a matching `unit_tests/modules/<name>/` directory.
- **Run:** `make test` (all), or `PYTHONPATH=. pytest -v unit_tests/modules/<name>/` (single module).
- **Framework:** pytest + unittest.mock. All async tests use `@pytest.mark.asyncio`.

### Unit test file naming

- One test file per source file: `app/modules/foo/bar.py` → `unit_tests/modules/foo/test_bar.py`.
- Utility files: `app/modules/foo/foo_utils.py` → `unit_tests/modules/foo/test_foo_utils.py`.
- Type files are rarely tested directly; focus on handler/route and utility files.

### Standard test structure for route/handler files

Each handler test file follows this exact pattern:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.<module>.<handler> import <handler_fn>
from app.common.responses import NotFoundException, InternalServerErrorException
from app.modules.<module>.<module>_types import <ResponseType>

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.app.state.db = MagicMock()
    req.app.state.logger = MagicMock()
    return req

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user123"
    return user

@pytest.mark.asyncio
async def test_<handler>_success(mock_request, mock_user, ...):
    # 1. Set up mock db collection and return values
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(return_value=update_result)
    collection.find_one = AsyncMock(return_value=updated_data)

    # 2. Call the handler
    result = await <handler_fn>(mock_request, ..., mock_user)

    # 3. Assert db calls
    mock_request.app.state.db.get_collection.assert_called_with("<collection_name>")
    collection.update_one.assert_called_once()
    collection.find_one.assert_called_once_with({"user_id": mock_user.id})

    # 4. Assert result type and key fields
    assert isinstance(result, <ResponseType>)
    assert result.<field> == <expected>

@pytest.mark.asyncio
async def test_<handler>_not_found(mock_request, mock_user, ...):
    update_result = MagicMock()
    update_result.matched_count = 0
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(return_value=update_result)

    with pytest.raises(NotFoundException):
        await <handler_fn>(mock_request, ..., mock_user)
    mock_request.app.state.logger.error.assert_called_with(...)

@pytest.mark.asyncio
async def test_<handler>_internal_error(mock_request, mock_user, ...):
    collection = mock_request.app.state.db.get_collection.return_value
    collection.update_one = AsyncMock(side_effect=Exception("db error"))

    with pytest.raises(InternalServerErrorException):
        await <handler_fn>(mock_request, ..., mock_user)
    mock_request.app.state.logger.error.assert_any_call(...)
```

Key conventions:

- **Three test cases per handler:** success, not_found (matched_count=0 or find_one returns None), internal_error (side_effect=Exception).
- **Mock `request`** via `MagicMock()` with `req.app.state.db` and `req.app.state.logger`. Add `req.app.state.env` if the handler reads env vars.
- **Mock `user`** via `MagicMock()` with `user.id = "user123"`.
- **Mock `body`** (if needed) via `MagicMock(spec=<RequestType>)` with `body.model_dump.return_value = {...}`.
- **DB mocking pattern:** `mock_request.app.state.db.get_collection.return_value` gives the collection mock. Then set `collection.find_one` / `collection.update_one` / `collection.insert_one` as `AsyncMock`.
- **Assert result is the Pydantic response type**, not a dict.
- **Assert logger was called** with the expected error message in error cases.

### Utility test structure

Utility tests often use class-based grouping:

```python
class Test<UtilityFunction>:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        collection = AsyncMock()
        db.get_collection.return_value = collection
        return db, collection

    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_<scenario>(self, mock_db, mock_logger, ...):
        ...
```

Or flat `@pytest.mark.parametrize` for data-transformation functions (see `test_notes_utils.py`).

### Auth tests

Auth tests are more complex and use `patch` for external dependencies (JWT encode/decode, GeminiApi, etc). See `test_auth_dependencies.py` and `test_auth_utils.py` for patterns:

- Use `@patch("app.modules.<module>.<file>.<ClassOrFn>")` to mock external SDKs.
- For multi-collection scenarios, use `get_collection.side_effect = lambda name: ...` to return different mocks per collection name.

## Acceptance tests

- **Location:** `acceptance_tests/` — flat structure, one file per feature area.
- **Run:** `make test-acc` (needs `make start-db` first).
- **Framework:** `TestClient` from Starlette, `respx` for HTTP mocking.
- **Fixtures in `conftest.py`:** `client` (auto-use TestClient), `user_email`, `login_user` (full login flow), `api_key`.
- **Session hooks:** `pytest_sessionstart` seeds static data (airports, aircrafts, airlines); `pytest_sessionfinish` drops the test DB.
- **Docker tests:** `make test-docker` uses `acceptance_tests/acc-test.docker-compose.yml` with its own MongoDB. CI runs only this.
- **`PK_ENV=test`** disables production-only behavior.

### Standard acceptance test patterns

Each test file groups related tests into classes (e.g. `TestUpdateGoals`, `TestAddChore`). Tests are synchronous (no `@pytest.mark.asyncio`).

**Standard test class structure:**

```python
class Test<Feature>:
    def test_<operation>_success(self, client, login_user):
        token, user_id, email = login_user

        # Optional: GET initial state first
        response = client.get("/<endpoint>", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        # Perform the operation
        body = {"field": "value"}
        response = client.post("/<endpoint>", headers={"Authorization": f"Bearer {token}"}, json=body)
        assert response.status_code == 201  # or 200 for PATCH/PUT/DELETE

        # Verify the response
        data = response.json()
        assert data["field"] == "value"

        # Optional: GET again to verify persistence
        response = client.get("/<endpoint>", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "value"
```

**Auth patterns:**

- Use `login_user` fixture for Bearer token auth: `headers={"Authorization": f"Bearer {token}"}`.
- Use `api_key` fixture for API key auth: `headers={"X-PK-Api-Key": api_key}`.
- For endpoints supporting both, write separate tests for each auth method.

**Reusable auth error cases:**

```python
AUTH_ERROR_CASES = [
    pytest.param({}, id="no_auth"),
    pytest.param({"X-PK-Api-Key": "pk_invalid_key"}, id="invalid_api_key"),
    pytest.param({"Authorization": "Bearer invalid.jwt.token"}, id="invalid_bearer"),
]

@pytest.mark.parametrize("headers", AUTH_ERROR_CASES)
def test_<operation>_auth_errors(self, client, headers):
    response = client.post("/<endpoint>", headers=headers, json={"field": "value"})
    assert response.status_code == 401
```

**Invalid body validation:**

```python
@pytest.mark.parametrize(
    "body,expected_status",
    [
        ({}, 422),  # All fields missing
        ({"field": -1}, 422),  # Negative value
        ({"field": "bad"}, 422),  # Wrong type
        ({"other": "value"}, 422),  # Missing required field
    ],
)
def test_<operation>_invalid_body(self, client, login_user, body, expected_status):
    token, *_ = login_user
    response = client.post("/<endpoint>", headers={"Authorization": f"Bearer {token}"}, json=body)
    assert response.status_code == expected_status
    if expected_status == 422:
        data = response.json()
        assert "detail" in data
```

**404 / not-found cases:**

```python
def test_<operation>_not_found(self, client, login_user):
    token, *_ = login_user
    response = client.delete("/<endpoint>/nonexistent_id", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    data = response.json()
    assert "Not Found: <ResourceName>" in data["detail"]
```

**Mocking external services:**

```python
from unittest.mock import patch

@patch("app.modules.<module>.<file>.<ClassOrFn>")
def test_<operation>_with_external_service(self, mock_cls, client, login_user):
    mock_cls.return_value.some_method = AsyncMock(return_value={...})
    token, *_ = login_user
    response = client.get("/<endpoint>", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
```

**Patching env vars on the app:**

```python
def test_<operation>_with_env_deps(self, client, login_user):
    client.app.state.env.SOME_API_KEY = "test-key"
    token, *_ = login_user
    # ...
```

**Key conventions:**

- Tests are **synchronous** — no `@pytest.mark.asyncio` (TestClient handles async internally).
- Always use `login_user` or `api_key` fixtures for authenticated endpoints.
- Assert `response.status_code` first, then `response.json()` for body checks.
- For 422 validation errors, assert `"detail" in data` (Pydantic returns a list of errors).
- For 404 errors, assert `"Not Found: <ResourceName>" in data["detail"]`.
- For CRUD flows: create → verify → update → verify → delete → verify.
- Auth error tests should use the shared `AUTH_ERROR_CASES` parametrize pattern.
