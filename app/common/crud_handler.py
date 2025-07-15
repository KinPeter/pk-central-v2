import uuid
from datetime import datetime, timezone
from logging import Logger
from typing import Callable
from fastapi import Request
from pymongo import ReturnDocument

from app.common.db import DbCollection
from app.common.responses import (
    IdResponse,
    InternalServerErrorException,
    ListResponse,
    NotFoundException,
)
from app.common.types import AsyncDatabase, PkBaseModel
from app.modules.auth.auth_types import CurrentUser


class CrudHandler[T]:
    def __init__(
        self,
        request: Request,
        user: CurrentUser,
        collection_name: DbCollection,
        entity_name: str,
    ):
        self.request = request
        self.user = user
        self.db: AsyncDatabase = request.app.state.db
        self.logger: Logger = request.app.state.logger
        self.collection = self.db.get_collection(collection_name)
        self.entity_name = entity_name

    async def get_listed(self, mapper_fn: Callable[[dict], T]) -> ListResponse[T]:
        """
        Retrieve a list of entities for the current user.
        """
        try:
            data = await self.collection.find({"user_id": self.user.id}).to_list(
                length=None
            )
            if not data:
                return ListResponse(entities=[])

            entities = [mapper_fn(item) for item in data]
            return ListResponse(entities=entities)

        except Exception as e:
            self.logger.error(
                f"Error retrieving {self.entity_name} list for user {self.user.id}: {e}"
            )
            raise InternalServerErrorException(
                f"An error occurred while retrieving the {self.entity_name} list: "
                + str(e)
            )

    async def get_single(self, id: str, mapper_fn: Callable[[dict], T]) -> T:
        """
        Retrieve a single entity by ID for the current user.
        """
        try:
            data = await self.collection.find_one({"user_id": self.user.id, "id": id})
            if not data:
                raise NotFoundException(resource=self.entity_name)

            return mapper_fn(data)

        except NotFoundException as e:
            raise e
        except Exception as e:
            self.logger.error(
                f"Error retrieving {self.entity_name} {id} for user {self.user.id}: {e}"
            )
            raise InternalServerErrorException(
                f"An error occurred while retrieving the {self.entity_name}: " + str(e)
            )

    async def create(
        self,
        body: PkBaseModel,
        mapper_fn: Callable[[dict], T],
        create_timestamp: bool = False,
    ) -> T:
        """
        Create a new entity for the current user.
        """
        try:
            entity_data = body.model_dump(
                exclude_none=False, exclude_unset=False, mode="json"
            )
            entity_data["id"] = str(uuid.uuid4())
            entity_data["user_id"] = self.user.id
            if create_timestamp:
                entity_data["created_at"] = datetime.now(timezone.utc).isoformat()

            result = await self.collection.insert_one(entity_data)
            if not result.acknowledged:
                raise InternalServerErrorException(
                    f"Failed to create {self.entity_name} for user {self.user.id}"
                )

            data = await self.collection.find_one({"_id": result.inserted_id})
            if not data:
                raise InternalServerErrorException(
                    f"Failed to retrieve created {self.entity_name} for user {self.user.id}"
                )

            return mapper_fn(data)

        except Exception as e:
            self.logger.error(
                f"Error creating {self.entity_name} for user {self.user.id}: {e}"
            )
            raise InternalServerErrorException(
                f"An error occurred while creating the {self.entity_name}: " + str(e)
            )

    async def update(
        self, id: str, body: PkBaseModel, mapper_fn: Callable[[dict], T]
    ) -> T:
        """
        Update an existing entity for the current user.
        """
        try:
            entity_data = body.model_dump(
                exclude_none=False, exclude_unset=True, mode="json"
            )
            result = await self.collection.find_one_and_update(
                {"user_id": self.user.id, "id": id},
                {"$set": entity_data},
                return_document=ReturnDocument.AFTER,
            )

            if not result:
                raise NotFoundException(resource=self.entity_name)

            return mapper_fn(result)

        except NotFoundException as e:
            raise e
        except Exception as e:
            self.logger.error(
                f"Error updating {self.entity_name} {id} for user {self.user.id}: {e}"
            )
            raise InternalServerErrorException(
                f"An error occurred while updating the {self.entity_name}: " + str(e)
            )

    async def delete(self, id: str) -> IdResponse:
        """
        Delete an entity by ID for the current user.
        """
        try:
            result = await self.collection.delete_one(
                {"user_id": self.user.id, "id": id}
            )

            if result.deleted_count == 0:
                raise NotFoundException(resource=self.entity_name)

            return IdResponse(id=id)

        except NotFoundException as e:
            raise e
        except Exception as e:
            self.logger.error(
                f"Error deleting {self.entity_name} {id} for user {self.user.id}: {e}"
            )
            raise InternalServerErrorException(
                f"An error occurred while deleting the {self.entity_name}: " + str(e)
            )
