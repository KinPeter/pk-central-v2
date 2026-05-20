# Guidelines for API modules

This document outlines the structure and conventions for API modules in the PK Central API v2 project. Each module corresponds to a specific feature area and defines its own FastAPI router, which is included in the main application.

## Module types

There are two main module patterns:

### 1. Simple CRUD modules

Standard Create/Read/Update/Delete operations on a single entity type. Examples: `notes`, `shortcuts`, `personal_data`, `birthdays`.

**Structure:**

```
app/modules/<name>/
├── __init__.py          # Empty (router imported directly from <name>.py)
├── <name>.py            # FastAPI router with all endpoint definitions
├── <name>_types.py      # Pydantic models (request/response types)
└── <name>_utils.py      # Mapper functions, helpers
```

### 2. Specialized modules

Modules with custom business logic, external API integrations, or non-standard operations. Examples: `activities`, `reddit`, `flights`, `trips`, `strava`, `visits`.

**Structure:**

```
app/modules/<name>/
├── __init__.py
├── <name>.py            # Router — delegates to handler files
├── <name>_types.py      # Pydantic models
├── <name>_utils.py      # Shared utilities, mapper functions, initial config creation
├── <name>_api.py        # (optional) External API client class
├── <handler>.py         # One file per endpoint/handler (e.g., get_activities.py, add_chore.py)
└── ...
```

## Creating a new module

### Step 1: Register the collection

Add the collection name to `DbCollection` enum in `app/common/db.py`:

```python
class DbCollection(str, Enum):
    # ... existing collections
    MY_MODULE = "my_module"
```

### Step 2: Create the module directory

```
app/modules/<name>/
├── __init__.py          # Empty file
├── <name>.py
├── <name>_types.py
└── <name>_utils.py
```

### Step 3: Define types (`<name>_types.py`)

All models must extend `PkBaseModel` from `app/common/types`. This provides automatic `snake_case` to `camelCase` alias conversion.

```python
from pydantic import Field
from app.common.responses import OkResponse
from app.common.types import BaseEntity, PkBaseModel

# Request model (what the client sends)
class MyEntityRequest(PkBaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_active: bool = True

# Response model (what the API returns) — extends BaseEntity for `id` field
class MyEntity(BaseEntity, MyEntityRequest):
    created_at: str
```

Key patterns:

- Use `PkBaseModel` for request bodies and standalone models
- Use `BaseEntity` (which extends `PkBaseModel`) for response models that have an `id`
- Use `OkResponse` as a mixin if you want logging on instantiation: `class MyEntity(OkResponse, BaseEntity): ...`
- Use `Field(...)` for required fields, `Field(default, ...)` for optional
- Validation constraints: `min_length`, `max_length`, `ge`, `le`, `gt`, `lt`

### Step 4: Define utilities (`<name>_utils.py`)

For simple CRUD modules, this typically contains only a mapper function:

```python
from app.modules.<name>.<name>_types import MyEntity

def to_my_entity(item: dict) -> MyEntity:
    return MyEntity(
        id=item["id"],
        created_at=item["created_at"],
        title=item.get("title"),
        description=item.get("description"),
        is_active=item.get("is_active", True),
    )
```

For specialized modules, also add:

- `create_initial_<name>_config(db, logger, user_id)` — creates default config for new users if needed
- Other shared helper functions

### Step 5: Define the router (`<name>.py`)

#### Simple CRUD module (using `CrudHandler`)

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.crud_handler import CrudHandler
from app.common.db import DbCollection
from app.common.responses import IdResponse, ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user_or_api_key
from app.modules.<name>.<name>_types import MyEntity, MyEntityRequest
from app.modules.<name>.<name>_utils import to_my_entity

router = APIRouter(tags=["MyModule"], prefix="/<name>")

@router.get(
    path="/",
    summary="Get My Entities",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_<name>(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> ListResponse[MyEntity]:
    return await CrudHandler[MyEntity](
        request=request,
        user=user,
        collection_name=DbCollection.<NAME>,
        entity_name="MyEntity",
    ).get_listed(mapper_fn=to_my_entity)

@router.post(
    path="/",
    summary="Create My Entity",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_create_<name>(
    request: Request,
    body: MyEntityRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> MyEntity:
    return await CrudHandler[MyEntity](
        request=request,
        user=user,
        collection_name=DbCollection.<NAME>,
        entity_name="MyEntity",
    ).create(body, mapper_fn=to_my_entity, create_timestamp=True)

@router.put(
    path="/{id}",
    summary="Update My Entity",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_<name>(
    request: Request,
    id: str,
    body: MyEntityRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> MyEntity:
    return await CrudHandler[MyEntity](
        request=request,
        user=user,
        collection_name=DbCollection.<NAME>,
        entity_name="MyEntity",
    ).update(id, body, mapper_fn=to_my_entity)

@router.delete(
    path="/{id}",
    summary="Delete My Entity",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_<name>(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> IdResponse:
    return await CrudHandler[MyEntity](
        request=request,
        user=user,
        collection_name=DbCollection.<NAME>,
        entity_name="MyEntity",
    ).delete(id)
```

#### Specialized module (delegating to handler files)

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from fastapi.params import Depends

from app.common.responses import ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user
from app.modules.<name>.<name>_types import MyConfig, MyConfigRequest
from app.modules.<name>.get_<name> import get_<name>
from app.modules.<name>.update_<name> import update_<name>

router = APIRouter(tags=["MyModule"], prefix="/<name>")

@router.get(
    path="/",
    summary="Get My Config",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_<name>(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> MyConfig:
    return await get_<name>(request, user)

@router.put(
    path="/",
    summary="Update My Config",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_<name>(
    request: Request,
    body: MyConfigRequest,
    user: Annotated[CurrentUser, Depends(auth_user)],
) -> MyConfig:
    return await update_<name>(request, body, user)
```

### Step 6: Register the router

In `app/main.py`, add the import and include the router:

```python
from app.modules.<name> import <name>

# ... in the app setup section:
app.include_router(<name>.router)
```

## Handler file patterns (specialized modules)

Each handler file in a specialized module follows this structure:

```python
from fastapi import Request

from app.common.db import DbCollection
from app.common.responses import InternalServerErrorException, NotFoundException
from app.modules.<name>.<name>_types import <ResponseType>
from app.modules.auth.auth_types import CurrentUser

async def <handler_name>(request: Request, ..., user: CurrentUser) -> <ResponseType>:
    """
    <Docstring describing what this handler does.>
    """
    db = request.app.state.db
    logger = request.app.state.logger

    try:
        collection = db.get_collection(DbCollection.<NAME>)
        # ... business logic ...

        return <ResponseType>(...)

    except NotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Error <doing something> for user {user.id}: {e}")
        raise InternalServerErrorException(
            "An error occurred while <doing something>: " + str(e)
        )
```

Key patterns:

- Access `db` via `request.app.state.db`
- Access `logger` via `request.app.state.logger`
- Always wrap in try/except, re-raise `NotFoundException`, catch all others as `InternalServerErrorException`
- Log errors with user context: `f"Error <action> for user {user.id}: {e}"`
- All documents are scoped by `user_id` — queries always include `{"user_id": user.id}`

## Authentication

Three auth dependencies are available in `app/modules/auth/auth_utils.py`:

| Dependency             | Use case                                                     |
| ---------------------- | ------------------------------------------------------------ |
| `auth_user`            | JWT Bearer token only                                        |
| `auth_user_or_api_key` | JWT Bearer OR `X-PK-Api-Key` header (API key takes priority) |
| `auth_api_key`         | API key only                                                 |

Usage in route:

```python
# JWT only
user: Annotated[CurrentUser, Depends(auth_user)]

# JWT or API key (most common for CRUD)
user: Annotated[CurrentUser, Depends(auth_user_or_api_key)]
```

## Response types

Available in `app/common/responses.py`:

| Type              | Use                                   |
| ----------------- | ------------------------------------- |
| `OkResponse`      | Base response with logging on init    |
| `ListResponse[T]` | Wraps `entities: list[T]`, logs count |
| `IdResponse`      | Returns `{"id": "..."}` after delete  |
| `MessageResponse` | Returns `{"message": "..."}`          |
| `ListModel[T]`    | Raw list wrapper without logging      |

Error exceptions (all extend `HTTPException`):

- `UnauthorizedException` — 401
- `ForbiddenOperationException` — 403
- `NotFoundException` — 404
- `ConflictException` — 409
- `InternalServerErrorException` — 500
- `NotImplementedException` — 501

Response docs for OpenAPI:

```python
responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response}
```

## CrudHandler

Located in `app/common/crud_handler.py`. Generic class `[T]` that handles standard CRUD with user scoping.

**Methods:**

- `get_listed(mapper_fn, projection=None)` — returns `ListResponse[T]`
- `get_single(id, mapper_fn, projection=None)` — returns `T`
- `create(body, mapper_fn, create_timestamp=False)` — returns `T`
- `update(id, body, mapper_fn)` — returns `T`
- `delete(id)` — returns `IdResponse`

**Key behavior:**

- All operations scoped to `user_id`
- `create()` auto-generates `id` (UUID4) and sets `user_id`
- `create(create_timestamp=True)` also sets `created_at` to current UTC ISO timestamp
- `update()` uses `exclude_unset=True` so only provided fields are updated
- `create()` uses `exclude_unset=False` so all fields including defaults are stored
- `mapper_fn` converts raw MongoDB dict to Pydantic model

## Adding initial config for new users

When a user is created, some modules need an initial config document. This is handled by a utility function called during user registration:

```python
async def create_initial_<name>_config(
    db: AsyncDatabase,
    logger: Logger,
    user_id: str,
):
    collection = db.get_collection(DbCollection.<NAME>)

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        # ... default values ...
    }

    existing = await collection.find_one({"user_id": user_id})
    if existing:
        logger.warning(f"<Name> config already exists for user {user_id}")
        raise ValueError(f"<Name> config already exists for user {user_id}")

    await collection.insert_one(data)
    logger.info(f"Initial <Name> config created for user {user_id}")
```

This function is called from the auth module during user creation. Register it in the appropriate place.

## External API integrations

For modules that call external services (e.g., `reddit`, `strava`), create a `<name>_api.py` with a class:

```python
class <Name>Api:
    def __init__(self, env: PkCentralEnv, logger: Logger):
        self.env = env
        self.logger = logger
        self.client = self._init_client()

    def _init_client(self) -> SomeClient | None:
        try:
            # Initialize using env vars like self.env.<NAME>_API_KEY
            return SomeClient(...)
        except Exception as e:
            self.logger.error(f"Failed to initialize <Name> API: {e}")
            return None

    async def close(self):
        if self.client:
            await self.client.close()
```

- Use `asyncpraw`, `aiohttp`, or similar async libraries
- Initialize in `main.py` lifespan if needed, or lazily in handlers
- Always handle initialization failures gracefully (return empty results, not 500)

## Testing

See `@rules/testing.md` for full testing guidelines. Quick summary:

### Unit tests

- Mirror `app/` structure in `unit_tests/`
- One test file per source file: `app/modules/foo/bar.py` → `unit_tests/modules/foo/test_bar.py`
- Use `MagicMock` for `request` and `user` fixtures
- Three test cases per handler: `success`, `not_found`, `internal_error`
- All async tests use `@pytest.mark.asyncio`
- Run: `make test` or `PYTHONPATH=. pytest -v unit_tests/modules/<name>/`

### Acceptance tests

- Flat structure in `acceptance_tests/`
- Use `TestClient` from Starlette
- Use `login_user` or `api_key` fixtures for auth
- Run: `make test-acc` (needs `make start-db`)
- Tests are synchronous (no `@pytest.mark.asyncio`)

## Naming conventions

| Element            | Convention                     | Example                               |
| ------------------ | ------------------------------ | ------------------------------------- |
| Module directory   | lowercase, underscore          | `personal_data/`                      |
| Router file        | `<name>.py`                    | `notes.py`                            |
| Types file         | `<name>_types.py`              | `activities_types.py`                 |
| Utils file         | `<name>_utils.py`              | `flights_utils.py`                    |
| Handler file       | `<action>_<entity>.py`         | `add_chore.py`, `get_flights.py`      |
| Route function     | `<method>_<action>_<entity>`   | `post_create_note`, `get_get_flights` |
| Mapper function    | `to_<entity>`                  | `to_note`, `to_flight`                |
| Pydantic request   | `<Entity>Request`              | `NoteRequest`, `ChoreRequest`         |
| Pydantic response  | `<Entity>` or `<Entity>Config` | `Note`, `ActivitiesConfig`            |
| DB collection enum | `UPPERCASE`                    | `DbCollection.NOTES`                  |

## Common patterns to follow

1. **User scoping**: Every DB query includes `{"user_id": user.id}` — users only see their own data
2. **Error handling**: Always try/except with specific `NotFoundException` re-raise
3. **Logging**: Log errors with user context, log success in `OkResponse` init
4. **UUID4 IDs**: Use `str(uuid.uuid4())` for new document IDs
5. **Pydantic serialization**: Use `body.model_dump(exclude_none=..., exclude_unset=..., mode="json")`
   - `exclude_unset=True` for updates (only changed fields)
   - `exclude_unset=False` for creates (all fields including defaults)
6. **No direct DB access in router**: Router delegates to handler files or `CrudHandler`
7. **Response types**: Always return typed Pydantic models, never raw dicts
