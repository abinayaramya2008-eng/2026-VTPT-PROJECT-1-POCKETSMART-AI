import os
from pathlib import Path

TEST_DB = Path("test_pocketsmart.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = "sqlite:///./test_pocketsmart.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-0123456789"
os.environ["MOCK_AI"] = "true"
