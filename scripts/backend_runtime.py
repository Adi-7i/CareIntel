"""Configuration checks and process lifecycle shared by the backend shell scripts."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import secrets
import signal
import socket
import ssl
import subprocess
import sys
import time
from pathlib import Path

import asyncpg
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from dotenv import dotenv_values
from pydantic import ValidationError
from pydantic_settings import SettingsError
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.engine import make_url

from careintel.core.config import Settings
from careintel.core.database import build_engine

ROOT = Path(__file__).resolve().parent.parent


def prepare_env() -> None:
    """Preserve existing credentials; initialize new files for local development."""
    path = ROOT / ".env"
    if not path.exists():
        content = (ROOT / ".env.example").read_text()
        values = {
            "SECRET_KEY": secrets.token_urlsafe(48),
            "JWT_SECRET_KEY": secrets.token_urlsafe(48),
            "LLM_PROVIDER": "demo",
            "EMBEDDING_PROVIDER": "demo",
            "STT_PROVIDER": "demo",
            "TTS_PROVIDER": "demo",
            "OCR_PROVIDER": "demo",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY": "",
        }
        for key, value in values.items():
            content = re.sub(rf"^{key}=.*$", f"{key}={value}", content, flags=re.MULTILINE)
        with open(path, "x", opener=lambda name, flags: os.open(name, flags, 0o600)) as file:
            file.write(content)
        print("Created development .env with random secrets and demo providers.")
        print("Set DATABASE_URL to your PostgreSQL database before completing setup.")
    else:
        print("Using existing .env; preserving credentials and provider choices.")
    path.chmod(0o600)

    # Older copies of the template supplied CSV, but Pydantic expects a JSON list.
    origins = dotenv_values(path).get("CORS_ALLOWED_ORIGINS")
    if origins and not origins.lstrip().startswith("["):
        converted = json.dumps([origin.strip() for origin in origins.split(",") if origin.strip()])
        content = re.sub(
            r"^CORS_ALLOWED_ORIGINS=.*$",
            f"CORS_ALLOWED_ORIGINS='{converted}'",
            path.read_text(),
            flags=re.MULTILINE,
        )
        path.write_text(content)
        print("Converted CORS_ALLOWED_ORIGINS to a JSON list, keeping the same origins.")


def load_settings() -> Settings:
    """Give actionable configuration errors without displaying secret input values."""
    try:
        settings = Settings()
    except ValidationError as exc:
        fields = sorted(
            {".".join(map(str, error["loc"])) or "configuration" for error in exc.errors()}
        )
        raise RuntimeError(
            f"Invalid settings: {', '.join(fields)}. Check .env and STARTUP.md."
        ) from None
    except SettingsError:
        raise RuntimeError(
            "Cannot parse settings. List values such as CORS_ALLOWED_ORIGINS must be JSON."
        ) from None
    database_url = settings.database_url.get_secret_value()
    if not database_url.startswith("postgresql+asyncpg://") or "<" in database_url:
        raise RuntimeError("Set DATABASE_URL to a real postgresql+asyncpg:// DSN in .env.")
    try:
        url = make_url(database_url)
        if not url.host or not url.database or not 1 <= (url.port or 5432) <= 65535:
            raise ValueError
    except (ValueError, TypeError):
        raise RuntimeError(
            "DATABASE_URL is malformed. Check its host, port and database name."
        ) from None
    keys = [settings.secret_key.get_secret_value(), settings.jwt_secret_key.get_secret_value()]
    if any(len(key) < 32 or "REPLACE" in key.upper() for key in keys) or keys[0] == keys[1]:
        raise RuntimeError(
            "Set SECRET_KEY and JWT_SECRET_KEY to different random secrets "
            "of at least 32 characters."
        )
    return settings


def check_revisions(heads: tuple[str, ...], *, require_head: bool) -> None:
    """Refuse unknown database history before attempting any schema changes."""
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    expected = set(scripts.get_heads())
    known = {revision.revision for revision in scripts.walk_revisions()}
    unknown = set(heads) - known
    if unknown:
        raise RuntimeError(
            f"Database revision(s) {', '.join(sorted(unknown))} are missing from this checkout "
            f"(repository head: {', '.join(sorted(expected))}). "
            "Use the matching code/migrations or configure a separate development database."
        )
    if require_head and set(heads) != expected:
        raise RuntimeError("Database schema is out of date. Run ./setup_backend.sh.")


def database_failure(exc: BaseException, settings: Settings) -> str:
    """Describe connection failures without copying server messages or secret DSNs."""
    url = make_url(settings.database_url.get_secret_value())
    target = f"{url.host}:{url.port or 5432}"
    reason = f"{type(exc).__name__}; check database availability and DATABASE_URL."
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, socket.gaierror):
            reason = "DNS lookup failed; check your internet connection, DNS and database hostname."
            break
        if isinstance(current, asyncpg.InvalidPasswordError):
            reason = (
                "authentication failed; check the database username and password in DATABASE_URL."
            )
            break
        if isinstance(current, asyncpg.InvalidAuthorizationSpecificationError) or (
            isinstance(current, asyncpg.PostgresError)
            and "tenant or user not found" in str(current).lower()
        ):
            reason = (
                "database user/tenant is invalid; check the username and pooler connection details."
            )
            break
        if isinstance(current, asyncpg.InvalidCatalogNameError):
            reason = "database does not exist; check the database name in DATABASE_URL."
            break
        if isinstance(current, asyncpg.InsufficientPrivilegeError):
            reason = "permission denied; the database user needs access to the application schema."
            break
        if isinstance(current, asyncpg.TooManyConnectionsError):
            reason = (
                "database connection limit reached; check the database/pooler connection limit."
            )
            break
        if isinstance(current, ssl.SSLError):
            reason = "TLS connection failed; check SSL settings and the database certificate."
            break
        if isinstance(current, ConnectionRefusedError):
            reason = "connection refused; check the database host, port and service status."
            break
        if isinstance(current, TimeoutError):
            reason = (
                "connection/check timed out after "
                f"{settings.dependency_connect_timeout_seconds:g}s; "
                "check internet access, firewall/VPN and database availability. "
                "If the service is slow, set DEPENDENCY_CONNECT_TIMEOUT_SECONDS=30 in .env."
            )
        elif isinstance(current, OSError):
            reason = "network connection failed; check internet access, routing and firewall/VPN."
        current = getattr(current, "orig", None) or current.__cause__ or current.__context__
    return f"PostgreSQL check failed for {target}: {reason}"


async def check_services(settings: Settings, *, schema: bool, workers: bool) -> None:
    """Verify dependencies with bounded waits and redacted errors."""
    try:
        import magic

        magic.from_buffer(b"CareIntel", mime=True)
    except (ImportError, OSError):
        raise RuntimeError("libmagic is unavailable. Rerun ./setup_backend.sh.") from None

    engine = build_engine(settings)
    try:
        async with asyncio.timeout(settings.dependency_connect_timeout_seconds):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                heads = await connection.run_sync(
                    lambda conn: MigrationContext.configure(conn).get_current_heads()
                )
                check_revisions(heads, require_head=schema)
                if schema:
                    vector = await connection.scalar(
                        text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                    )
                    if not vector:
                        raise RuntimeError(
                            "Database pgvector extension is missing. Run ./setup_backend.sh."
                        )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(database_failure(exc, settings)) from None
    finally:
        await engine.dispose()
    print("PostgreSQL OK" + ("; migrations at repository head; pgvector OK." if schema else "."))

    if workers or settings.redis_url:
        url = (
            settings.redis_url.get_secret_value()
            if settings.redis_url
            else settings.celery_broker_url.get_secret_value()
        )
        urls = {url}
        if workers and not settings.redis_url and settings.celery_result_backend:
            urls.add(settings.celery_result_backend.get_secret_value())
        for redis_url in urls:
            client = Redis.from_url(
                redis_url, socket_connect_timeout=settings.dependency_connect_timeout_seconds
            )
            try:
                async with asyncio.timeout(settings.dependency_connect_timeout_seconds):
                    await client.ping()
            except Exception:
                raise RuntimeError(
                    "Redis check failed. Check REDIS_URL/CELERY_BROKER_URL "
                    "and service availability."
                ) from None
            finally:
                await client.aclose()
        print("Redis OK.")


def supervise(commands: list[tuple[str, list[str]]]) -> int:
    """Stop the entire service set on Ctrl-C, termination, or any child exit."""
    processes: list[tuple[str, subprocess.Popen[bytes]]] = []
    stop_signal: int | None = None

    def request_stop(signum: int, _frame: object) -> None:
        nonlocal stop_signal
        stop_signal = signum

    previous = {sig: signal.signal(sig, request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for name, command in commands:
            if stop_signal is not None:
                break
            print(f"Starting {name}...", flush=True)
            # Commands use this environment's Python with fixed modules and no shell.
            process = subprocess.Popen(command, cwd=ROOT, start_new_session=True)  # noqa: S603
            processes.append((name, process))
        while stop_signal is None:
            for name, process in processes:
                result = process.poll()
                if result is not None:
                    print(f"{name} exited ({result}); stopping backend services.", file=sys.stderr)
                    return result if result > 0 else 1
            time.sleep(0.25)
        return 130 if stop_signal == signal.SIGINT else 143
    finally:
        print("Stopping backend services...", flush=True)
        for _name, process in processes:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 30
        for _name, process in processes:
            try:
                process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main() -> int:
    os.chdir(ROOT)
    parser = argparse.ArgumentParser(description="CareIntel backend setup and startup.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("prepare-env")
    check = subcommands.add_parser("check")
    check.add_argument("--before-migrations", action="store_true")
    start = subcommands.add_parser(
        "start",
        description="Start API; automatically start worker and dispatcher when REDIS_URL is set.",
    )
    start.add_argument("--host", help="Override APP_HOST")
    start.add_argument("--port", type=int, help="Override APP_PORT")
    start.add_argument("--reload", action="store_true", help="Enable API reload in development")
    start.add_argument("--check", action="store_true", help="Check configuration/services and exit")
    workers = start.add_mutually_exclusive_group()
    workers.add_argument("--api-only", action="store_true", help="Start only the API")
    workers.add_argument(
        "--with-workers",
        action="store_true",
        help="Start worker/dispatcher, using the fallback broker if needed",
    )
    args = parser.parse_args()
    if args.command == "prepare-env":
        prepare_env()
        return 0
    settings = load_settings()
    with_workers = bool(settings.redis_url)
    if args.command == "check":
        asyncio.run(
            check_services(settings, schema=not args.before_migrations, workers=with_workers)
        )
        return 0
    with_workers = not args.api_only and (with_workers or args.with_workers)
    if args.reload and settings.is_production:
        raise RuntimeError("--reload is not allowed in production.")
    port = settings.app_port if args.port is None else args.port
    if not 1 <= port <= 65535:
        raise RuntimeError("Port must be between 1 and 65535.")
    asyncio.run(check_services(settings, schema=True, workers=with_workers))
    if args.check:
        print("Backend checks passed.")
        return 0
    host = args.host or settings.app_host
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "careintel.main:app",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        settings.app_log_level.value.lower(),
    ]
    if args.reload:
        command.extend(["--reload", "--reload-dir", str(ROOT / "src")])
    commands = [("API", command)]
    if with_workers:
        queues = ",".join(
            dict.fromkeys(
                [
                    settings.celery_task_default_queue,
                    "careintel_default",
                    "careintel_processing",
                    "careintel_retrieval",
                    "careintel_ai",
                    "careintel_workflow",
                ]
            )
        )
        commands.extend(
            [
                (
                    "Celery worker",
                    [
                        sys.executable,
                        "-m",
                        "celery",
                        "-A",
                        "careintel.workers.celery_app:celery_app",
                        "worker",
                        "--loglevel",
                        settings.app_log_level.value,
                        "--concurrency",
                        "2",
                        "-Q",
                        queues,
                    ],
                ),
                (
                    "outbox dispatcher",
                    [sys.executable, "-m", "careintel.workers.outbox_runner", "--interval", "2"],
                ),
            ]
        )
    else:
        print("API only. Set REDIS_URL or use --with-workers for asynchronous execution.")
    # This comparison only formats a URL; the bind address comes from settings/CLI.
    display_host = "127.0.0.1" if host == "0.0.0.0" else f"[{host}]" if ":" in host else host  # noqa: S104
    print(f"API docs: http://{display_host}:{port}/api/docs (available after API startup)")
    print("Press Ctrl-C to stop all services.")
    return supervise(commands)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError) as exc:
        print(f"Backend error: {exc}", file=sys.stderr)
        sys.exit(1)
