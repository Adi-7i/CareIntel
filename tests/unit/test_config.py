# mypy: ignore-errors
"""Unit tests for Settings configuration."""

from __future__ import annotations

import pytest

from careintel.core.config import Environment, LogLevel, Settings


@pytest.mark.unit
class TestSettings:
    """Typed configuration unit tests."""

    def test_loads_with_valid_config(self) -> None:
        """Settings constructs successfully with all required fields."""
        s = Settings(  # type: ignore[call-arg,arg-type]
            app_env=Environment.DEVELOPMENT,
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            secret_key="some-long-secret-key",
        )
        assert s.app_env == Environment.DEVELOPMENT
        assert s.app_port == 8000
        assert s.app_log_level == LogLevel.INFO

    def test_rejects_sync_database_url(self) -> None:
        """Synchronous PostgreSQL driver scheme is rejected at validation time."""
        with pytest.raises(ValueError, match="asyncpg"):
            Settings(  # type: ignore[call-arg,arg-type]
                database_url="postgresql://user:pass@localhost:5432/db",
                secret_key="some-secret",
            )

    def test_rejects_debug_in_production(self) -> None:
        """Debug mode in production raises a clear validation error."""
        with pytest.raises(ValueError, match="app_debug"):
            Settings(  # type: ignore[call-arg,arg-type]
                app_env=Environment.PRODUCTION,
                app_debug=True,
                database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
                secret_key="some-secret",
            )

    def test_rejects_sql_echo_in_production(self) -> None:
        """SQL echo in production raises a clear validation error."""
        with pytest.raises(ValueError, match="database_echo_sql"):
            Settings(  # type: ignore[call-arg,arg-type]
                app_env=Environment.PRODUCTION,
                app_debug=False,
                database_echo_sql=True,
                database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
                secret_key="some-secret",
            )

    def test_database_url_safe_masks_credentials(self) -> None:
        """database_url_safe() returns the URL with credentials redacted."""
        s = Settings(  # type: ignore[call-arg,arg-type]
            database_url="postgresql+asyncpg://admin:supersecret@db.host:5432/mydb",
            secret_key="some-secret",
        )
        safe = s.database_url_safe()
        assert "supersecret" not in safe
        assert "admin" not in safe
        assert "***:***@" in safe
        assert "db.host:5432/mydb" in safe

    def test_is_production_flag(self) -> None:
        """is_production returns True only for production environment."""
        prod = Settings(  # type: ignore[call-arg,arg-type]
            app_env=Environment.PRODUCTION,
            app_debug=False,
            database_url="postgresql+asyncpg://u:p@h:5432/d",
            secret_key="a-very-long-secret-key-for-production-environment",
        )
        assert prod.is_production is True

        dev = Settings(  # type: ignore[call-arg,arg-type]
            database_url="postgresql+asyncpg://u:p@h:5432/d",
            secret_key="some-secret",
        )
        assert dev.is_production is False

    def test_production_rejects_demo_provider_fallback(self) -> None:
        """Production cannot silently run configured AI capabilities on demos."""
        with pytest.raises(ValueError, match="LLM_PROVIDER"):
            Settings(  # type: ignore[call-arg,arg-type]
                _env_file=None,
                app_env=Environment.PRODUCTION,
                database_url="postgresql+asyncpg://u:p@h:5432/d",
                secret_key="production-secret-key",
                jwt_secret_key="production-jwt-secret-key",
                azure_storage_connection_string="UseDevelopmentStorage=true",
                redis_url="redis://redis.example:6379/0",
            )

    def test_production_accepts_fully_configured_external_providers(self) -> None:
        """A complete external-provider configuration passes fail-closed guards."""
        settings = Settings(  # type: ignore[call-arg,arg-type]
            _env_file=None,
            app_env=Environment.PRODUCTION,
            database_url="postgresql+asyncpg://u:p@h:5432/d",
            secret_key="production-secret-key",
            jwt_secret_key="production-jwt-secret-key",
            azure_storage_connection_string="UseDevelopmentStorage=true",
            redis_url="redis://redis.example:6379/0",
            llm_provider="azure_openai",
            embedding_provider="azure_openai",
            tts_provider="azure_openai",
            stt_provider="azure_openai_transcribe",
            ocr_provider="azure_document_intelligence",
            azure_openai_api_key="synthetic-key",
            azure_document_intelligence_endpoint="https://example.invalid",
            azure_document_intelligence_key="synthetic-key",
        )

        assert settings.is_production is True

    def test_is_testing_flag(self) -> None:
        """is_testing returns True only for testing environment."""
        from careintel.core.config import Environment

        test = Settings(  # type: ignore[call-arg,arg-type]
            app_env=Environment.TESTING,
            database_url="postgresql+asyncpg://u:p@h:5432/d",
            secret_key="some-secret",
        )
        assert test.is_testing is True

    def test_secret_key_is_secret_str(self) -> None:
        """secret_key is a SecretStr — str() does not reveal the value."""
        s = Settings(  # type: ignore[call-arg,arg-type]
            database_url="postgresql+asyncpg://u:p@h:5432/d",
            secret_key="my-super-secret",
        )
        assert "my-super-secret" not in str(s.secret_key)
        assert s.secret_key.get_secret_value() == "my-super-secret"

    def test_database_url_is_secret_str(self) -> None:
        """database_url is a SecretStr — str() does not reveal credentials."""
        s = Settings(  # type: ignore[call-arg,arg-type]
            database_url="postgresql+asyncpg://admin:pass@host/db",
            secret_key="some-secret",
        )
        assert "pass" not in str(s.database_url)

    def test_cors_allowed_origins_defaults_empty(self) -> None:
        """CORS origins default to an empty list."""
        s = Settings(  # type: ignore[call-arg,arg-type]
            database_url="postgresql+asyncpg://u:p@h:5432/d",
            secret_key="some-secret",
        )
        assert s.cors_allowed_origins == []

    def test_cors_allowed_origins_accepts_list(self) -> None:
        """CORS origins can be configured."""
        s = Settings(  # type: ignore[call-arg,arg-type]
            database_url="postgresql+asyncpg://u:p@h:5432/d",
            secret_key="some-secret",
            cors_allowed_origins=["http://localhost:3000"],
        )
        assert "http://localhost:3000" in s.cors_allowed_origins
