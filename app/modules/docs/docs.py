from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.common.crud_handler import CrudHandler
from app.common.db import DbCollection
from app.common.responses import IdResponse, ListResponse, ResponseDocs
from app.modules.auth.auth_types import CurrentUser
from app.modules.auth.auth_utils import auth_user_or_api_key
from app.modules.docs.docs_types import (
    Document,
    DocumentListItem,
    DocumentRequest,
    docs_list_item_projection,
)
from app.modules.docs.docs_utils import to_document, to_document_list_item


router = APIRouter(tags=["Documents"], prefix="/docs")


@router.get(
    path="/",
    summary="Get Documents",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_documents(
    request: Request,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> ListResponse[DocumentListItem]:
    """
    Get the list of documents for the user.
    Content is not included in this response.
    """
    return await CrudHandler[DocumentListItem](
        request=request,
        user=user,
        collection_name=DbCollection.DOCUMENTS,
        entity_name="Document",
    ).get_listed(mapper_fn=to_document_list_item, projection=docs_list_item_projection)


@router.get(
    path="/{id}",
    summary="Get Document content by ID",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def get_get_document_by_id(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> Document:
    """
    Get a specific document by its ID.
    Content is included in this response.
    """
    return await CrudHandler[Document](
        request=request,
        user=user,
        collection_name=DbCollection.DOCUMENTS,
        entity_name="Document",
    ).get_single(id, mapper_fn=to_document)


@router.post(
    path="/",
    summary="Create Document",
    status_code=status.HTTP_201_CREATED,
    responses={**ResponseDocs.unauthorized_response},
)
async def post_create_document(
    request: Request,
    body: DocumentRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> Document:
    """
    Create a new document for the user.
    """
    return await CrudHandler[Document](
        request=request,
        user=user,
        collection_name=DbCollection.DOCUMENTS,
        entity_name="Document",
    ).create(body, mapper_fn=to_document)


@router.put(
    path="/{id}",
    summary="Update Document",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def put_update_document(
    request: Request,
    id: str,
    body: DocumentRequest,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> Document:
    """
    Update an existing document for the user.
    """
    return await CrudHandler[Document](
        request=request,
        user=user,
        collection_name=DbCollection.DOCUMENTS,
        entity_name="Document",
    ).update(id, body, mapper_fn=to_document)


@router.delete(
    path="/{id}",
    summary="Delete Document",
    status_code=status.HTTP_200_OK,
    responses={**ResponseDocs.unauthorized_response, **ResponseDocs.not_found_response},
)
async def delete_delete_document(
    request: Request,
    id: str,
    user: Annotated[CurrentUser, Depends(auth_user_or_api_key)],
) -> IdResponse:
    """
    Delete a document for the user.
    """
    return await CrudHandler[Document](
        request=request,
        user=user,
        collection_name=DbCollection.DOCUMENTS,
        entity_name="Document",
    ).delete(id)
