"""Rollback-only verification of database audit modification enforcement."""

from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

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

            update_blocked = False
            try:
                await connection.execute(
                    text("UPDATE audit_logs SET outcome = outcome WHERE id = :audit_id"),
                    {"audit_id": audit_id},
                )
            except DBAPIError:
                update_blocked = True
            finally:
                await connection.rollback()

            delete_blocked = False
            try:
                await connection.execute(
                    text("DELETE FROM audit_logs WHERE id = :audit_id"),
                    {"audit_id": audit_id},
                )
            except DBAPIError:
                delete_blocked = True
            finally:
                await connection.rollback()

            row_still_exists = (
                await connection.execute(
                    text("SELECT count(*) FROM audit_logs WHERE id = :audit_id"),
                    {"audit_id": audit_id},
                )
            ).scalar_one() == 1

        print("rollback_after_each_attempt: PASS")
        print(f"database_update_blocked: {'PASS' if update_blocked else 'FAIL'}")
        print(f"database_delete_blocked: {'PASS' if delete_blocked else 'FAIL'}")
        print(f"audit_row_preserved: {'PASS' if row_still_exists else 'FAIL'}")
        print("application_repository_append_only: static design only")
        raise SystemExit(0 if update_blocked and delete_blocked and row_still_exists else 1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
