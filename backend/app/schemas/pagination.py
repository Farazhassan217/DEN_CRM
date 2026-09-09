from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field
import math

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized pagination response envelope."""
    data: List[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., description="Total count of items matching the query")
    page: int = Field(1, description="Current page number (1-indexed)")
    limit: int = Field(20, description="Items per page")
    total_pages: int = Field(1, description="Total number of pages")

    @classmethod
    def create(cls, items: List[T], total: int, page: int, limit: int):
        safe_limit = max(limit, 1)
        safe_page = max(page, 1)
        total_pages = math.ceil(total / safe_limit) if total > 0 else 1
        return cls(
            data=items,
            total=total,
            page=safe_page,
            limit=safe_limit,
            total_pages=total_pages
        )
