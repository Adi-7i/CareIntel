"""Configuration preservation and process shutdown for the local launch scripts."""

from __future__ import annotations

import importlib.util
import json
import os
import signal
import socket
import ssl
import subprocess
import sys
import time
from pathlib import Path

import asyncpg
import pytest
from dotenv import dotenv_values
from sqlalchemy.exc import OperationalError

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "backend_runtime.py"
spec = importlib.util.spec_from_file_location("backend_runtime", SCRIPT)
assert spec is not None and spec.loader is not None
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


@pytest.mark.unit
def test_existing_env_preserves_credentials_and_cors_origins(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    path = tmp_path / ".env"
    path.write_text(
        "SECRET_KEY=existing-key\n"
        "LLM_PROVIDER=azure_openai\n"
        "CORS_ALLOWED_ORIGINS=http://localhost:3000,https://example.com\n"
    )
    runtime.prepare_env()
    first_content = path.read_text()
    runtime.prepare_env()
    assert path.read_text() == first_content
    values = dotenv_values(path)
    assert values["SECRET_KEY"] == "existing-key"
    assert values["LLM_PROVIDER"] == "azure_openai"
    assert json.loads(values["CORS_ALLOWED_ORIGINS"]) == [
        "http://localhost:3000",
        "https://example.com",
    ]
    assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.unit
def test_new_env_uses_unique_secrets_and_explicit_demo_providers(tmp_path, monkeypatch):
    template = SCRIPT.parent.parent / ".env.example"
    (tmp_path / ".env.example").write_text(template.read_text())
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    runtime.prepare_env()
    values = dotenv_values(tmp_path / ".env")
    assert len(values["SECRET_KEY"]) >= 32
    assert len(values["JWT_SECRET_KEY"]) >= 32
    assert values["SECRET_KEY"] != values["JWT_SECRET_KEY"]
    for key in (
        "LLM_PROVIDER",
        "EMBEDDING_PROVIDER",
        "STT_PROVIDER",
        "TTS_PROVIDER",
        "OCR_PROVIDER",
    ):
        assert values[key] == "demo"
    assert values["AZURE_OPENAI_API_KEY"] == ""


@pytest.mark.unit
def test_unknown_database_revision_is_rejected_before_migrations():
    with pytest.raises(RuntimeError, match="missing from this checkout"):
        runtime.check_revisions(("unknown-revision",), require_head=False)


@pytest.mark.unit
def test_fresh_database_is_allowed_for_setup_but_requires_migrations_to_start():
    runtime.check_revisions((), require_head=False)
    with pytest.raises(RuntimeError, match=r"Run \./setup_backend\.sh"):
        runtime.check_revisions((), require_head=True)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (socket.gaierror(-2, "private input"), "DNS lookup failed"),
        (TimeoutError("private input"), "timed out"),
        (asyncpg.InvalidPasswordError("private input"), "authentication failed"),
        (asyncpg.InvalidCatalogNameError("private input"), "database does not exist"),
        (ssl.SSLError("private input"), "TLS connection failed"),
        (ConnectionRefusedError("private input"), "connection refused"),
        (OSError("private input"), "network connection failed"),
        (ValueError("private input"), "OperationalError"),
    ],
)
def test_database_failure_reports_specific_cause_without_secrets(error, expected):
    from unittest.mock import MagicMock

    settings = MagicMock()
    settings.database_url.get_secret_value.return_value = (
        "postgresql+asyncpg://private-user:private-password@db.example.com:5432/private-db"
    )
    settings.dependency_connect_timeout_seconds = 10
    wrapped = OperationalError("private statement", {}, error)
    message = runtime.database_failure(wrapped, settings)
    assert expected in message
    assert "db.example.com:5432" in message
    assert "private" not in message


@pytest.mark.unit
@pytest.mark.parametrize("stop_with_signal", [False, True])
def test_supervisor_stops_other_processes_on_failure_or_termination(tmp_path, stop_with_signal):
    marker = tmp_path / "child.pid"
    child = (
        "import os,time; from pathlib import Path; "
        f"Path({str(marker)!r}).write_text(str(os.getpid())); time.sleep(60)"
    )
    failing_child = "import time; time.sleep(1); raise SystemExit(7)"
    commands = [("long-lived", [sys.executable, "-c", child])]
    if not stop_with_signal:
        commands.append(("failed", [sys.executable, "-c", failing_child]))
    launcher = (
        "import importlib.util; "
        f"spec=importlib.util.spec_from_file_location('runtime', {str(SCRIPT)!r}); "
        "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
        f"raise SystemExit(module.supervise({commands!r}))"
    )
    parent = subprocess.Popen([sys.executable, "-c", launcher])
    child_pid = None
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.exists(), "Supervised child did not start"
        child_pid = int(marker.read_text())
        if stop_with_signal:
            parent.send_signal(signal.SIGTERM)
        assert parent.wait(timeout=10) == (143 if stop_with_signal else 7)
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait()
        if child_pid is not None:
            try:
                os.killpg(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
