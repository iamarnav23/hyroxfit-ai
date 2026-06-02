"""Database placeholder for Stage 4 MVP v1.

Supabase/PostgreSQL will be connected in a later stage. Keeping this file now
makes the folder structure ready without adding database complexity too early.
"""


def get_database_status() -> dict:
    """Return a simple message until the real database is connected."""
    return {
        "connected": False,
        "message": "Database is not connected in Stage 4 MVP v1",
    }
