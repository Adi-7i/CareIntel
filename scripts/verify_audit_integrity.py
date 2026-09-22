"""Rollback-only verification of database audit modification enforcement."""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from careintel.core.config import get_settings
from careintel.core.database import build_engine


async def main() -> None:
    engine = build_engine(get_settings())
    try:
        async with engine.connect() as connection:
            audit_id = (
                await connection.execute(
                    text("SELECT id FROM audit_logs ORDER BY occurred_at DESC LIMIT 1")
                )
            ).scalar_one_or_none()
            if audit_id is None:
                print("audit_row_available: NOT VERIFIED")
                raise SystemExit(1)

            update_result = await connection.execute(
                text("UPDATE audit_logs SET outcome = outcome WHERE id = :audit_id"),
                {"audit_id": audit_id},
            )
            await connection.rollback()

            delete_result = await connection.execute(
                text("DELETE FROM audit_logs WHERE id = :audit_id"),
                {"audit_id": audit_id},
            )
            await connection.rollback()

        update_blocked = update_result.rowcount == 0
        delete_blocked = delete_result.rowcount == 0
        print("rollback_after_each_attempt: PASS")
        print(f"database_update_blocked: {'PASS' if update_blocked else 'FAIL'}")
        print(f"database_delete_blocked: {'PASS' if delete_blocked else 'FAIL'}")
        print("application_repository_append_only: static design only")
        raise SystemExit(0 if update_blocked and delete_blocked else 1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
