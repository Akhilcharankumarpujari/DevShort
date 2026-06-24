from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.session import engine


async def check_database_health(db_engine: AsyncEngine = engine) -> dict[str, Any]:
    try:
        async with db_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        return {
            "status": "down",
            "error": exc.__class__.__name__,
        }
    return {"status": "up"}
