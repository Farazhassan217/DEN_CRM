import pytest
from app.core.cache import CacheManager

def test_cache_set_get_and_invalidation():
    """Verify that CacheManager correctly caches data and supports prefix invalidation."""
    prefix = "clinics"
    clinic_id = "clinic_abc_123"
    data = {"id": clinic_id, "name": "Dental Smile Clinic", "phone": "+123456789"}

    # Set cache
    success = CacheManager.set(prefix, clinic_id, data, ttl=10)
    assert success is True

    # Retrieve cache
    cached = CacheManager.get(prefix, clinic_id)
    assert cached == data

    # Invalidate
    CacheManager.invalidate(prefix, clinic_id)
    assert CacheManager.get(prefix, clinic_id) is None
