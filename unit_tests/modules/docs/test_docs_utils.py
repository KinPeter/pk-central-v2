import pytest
from app.modules.docs.docs_utils import to_document_list_item, to_document
from app.modules.docs.docs_types import Document, DocumentListItem


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "item,expected",
    [
        # All fields present with multiple tags
        (
            {
                "_id": "507f1f77bcf86cd799439011",
                "id": "doc1",
                "title": "Test Document",
                "tags": ["python", "testing", "pytest"],
                "user_id": "user123",
                "created_by": "admin",
            },
            {
                "id": "doc1",
                "title": "Test Document",
                "tags": ["python", "testing", "pytest"],
            },
        ),
        # Only required fields (no tags)
        (
            {
                "_id": "507f1f77bcf86cd799439012",
                "id": "doc2",
                "title": "Minimal Document",
                "user_id": "user456",
            },
            {
                "id": "doc2",
                "title": "Minimal Document",
                "tags": [],
            },
        ),
        # With empty tags list
        (
            {
                "_id": "507f1f77bcf86cd799439013",
                "id": "doc3",
                "title": "Document with Empty Tags",
                "tags": [],
                "user_id": "user789",
                "metadata": {"some": "data"},
            },
            {
                "id": "doc3",
                "title": "Document with Empty Tags",
                "tags": [],
            },
        ),
        # With single tag
        (
            {
                "_id": "507f1f77bcf86cd799439014",
                "id": "doc4",
                "title": "Single Tag Document",
                "tags": ["important"],
                "user_id": "user101",
                "extra_field": "should be removed",
            },
            {
                "id": "doc4",
                "title": "Single Tag Document",
                "tags": ["important"],
            },
        ),
    ],
)
async def test_to_document_list_item(item, expected):
    doc_list_item = to_document_list_item(item)
    assert isinstance(doc_list_item, DocumentListItem)
    assert doc_list_item.id == expected["id"]
    assert doc_list_item.title == expected["title"]
    assert doc_list_item.tags == expected["tags"]
    # Verify unwanted fields are not present
    assert not hasattr(doc_list_item, "_id")
    assert not hasattr(doc_list_item, "user_id")
    assert not hasattr(doc_list_item, "created_by")
    assert not hasattr(doc_list_item, "metadata")
    assert not hasattr(doc_list_item, "extra_field")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "item,expected",
    [
        # All fields present with multiple tags
        (
            {
                "_id": "507f1f77bcf86cd799439011",
                "id": "doc1",
                "title": "Test Document",
                "tags": ["python", "testing", "pytest"],
                "content": "This is a test document with detailed content.",
                "user_id": "user123",
                "created_by": "admin",
            },
            {
                "id": "doc1",
                "title": "Test Document",
                "tags": ["python", "testing", "pytest"],
                "content": "This is a test document with detailed content.",
            },
        ),
        # Only required fields (no tags)
        (
            {
                "_id": "507f1f77bcf86cd799439012",
                "id": "doc2",
                "title": "Minimal Document",
                "content": "Minimal content",
                "user_id": "user456",
            },
            {
                "id": "doc2",
                "title": "Minimal Document",
                "tags": [],
                "content": "Minimal content",
            },
        ),
        # With empty tags list
        (
            {
                "_id": "507f1f77bcf86cd799439013",
                "id": "doc3",
                "title": "Document with Empty Tags",
                "tags": [],
                "content": "Some content here",
                "user_id": "user789",
                "metadata": {"some": "data"},
            },
            {
                "id": "doc3",
                "title": "Document with Empty Tags",
                "tags": [],
                "content": "Some content here",
            },
        ),
        # With single tag
        (
            {
                "_id": "507f1f77bcf86cd799439014",
                "id": "doc4",
                "title": "Single Tag Document",
                "tags": ["important"],
                "content": "Important document content with longer text.",
                "user_id": "user101",
                "extra_field": "should be removed",
            },
            {
                "id": "doc4",
                "title": "Single Tag Document",
                "tags": ["important"],
                "content": "Important document content with longer text.",
            },
        ),
        # With long content
        (
            {
                "_id": "507f1f77bcf86cd799439015",
                "id": "doc5",
                "title": "Long Content Document",
                "tags": ["guide", "tutorial"],
                "content": "This is a very long document content.\n\nWith multiple paragraphs.\n\nAnd detailed instructions.",
                "user_id": "user202",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "doc5",
                "title": "Long Content Document",
                "tags": ["guide", "tutorial"],
                "content": "This is a very long document content.\n\nWith multiple paragraphs.\n\nAnd detailed instructions.",
            },
        ),
    ],
)
async def test_to_document(item, expected):
    document = to_document(item)
    assert isinstance(document, Document)
    assert document.id == expected["id"]
    assert document.title == expected["title"]
    assert document.tags == expected["tags"]
    assert document.content == expected["content"]
    # Verify unwanted fields are not present
    assert not hasattr(document, "_id")
    assert not hasattr(document, "user_id")
    assert not hasattr(document, "created_by")
    assert not hasattr(document, "metadata")
    assert not hasattr(document, "extra_field")
    assert not hasattr(document, "updated_at")
