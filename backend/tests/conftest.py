import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.core.redis_client import redis_client

@pytest.fixture(autouse=True)
def clean_redis():
    """Flush redis fallback before each test."""
    redis_client.flushdb()
    yield
    redis_client.flushdb()

@pytest.fixture
def client():
    """FastAPI TestClient."""
    return TestClient(app, raise_server_exceptions=False)
