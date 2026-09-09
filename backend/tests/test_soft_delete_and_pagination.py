import pytest
from app.schemas.pagination import PaginatedResponse

def test_paginated_response_schema():
    """Verify PaginatedResponse calculates total_pages and preserves pagination contract."""
    items = [{"id": 1}, {"id": 2}, {"id": 3}]
    resp = PaginatedResponse.create(items=items, total=25, page=1, limit=10)
    
    assert resp.total == 25
    assert resp.page == 1
    assert resp.limit == 10
    assert resp.total_pages == 3
    assert len(resp.data) == 3
