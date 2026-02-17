"""
Pytest configuration. Sets AUTH_DISABLED so tests run without Auth0.
Uses a temp file for SQLite so tests have a persistent database to reset.
"""

import os
import tempfile

# Disable auth during tests so existing tests pass without token
os.environ.setdefault("AUTH_DISABLED", "1")
# Use a temp file for tests (in-memory DB is freed when connection closes)
if "DB_PATH" not in os.environ:
    _test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _test_db.close()
    os.environ["DB_PATH"] = _test_db.name
