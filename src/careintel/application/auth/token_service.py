"""
JWT Token service.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

import jwt
from ulid import ULID

from careintel.core.config import Settings
from careintel.core.errors import AuthError
from careintel.domain.auth.models import TokenClaims


class JWTService:
    """Service for issuing and validating JWT access tokens."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.secret_key = settings.jwt_secret_key.get_secret_value()
        self.algorithm = settings.jwt_algorithm
        self.issuer = settings.jwt_issuer
        self.audience = settings.jwt_audience
        self.ttl_minutes = settings.jwt_access_token_ttl_minutes

    def issue_token(self, user_id: uuid.UUID, session_id: uuid.UUID) -> str:
        """Issue a new access token for a session."""
        now = datetime.datetime.now(datetime.UTC)
        expires = now + datetime.timedelta(minutes=self.ttl_minutes)
        jti = str(ULID())

        claims = {
            "sub": str(user_id),
            "sid": str(session_id),
            "jti": jti,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": expires,
            "type": "access",
        }

        return jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> TokenClaims:
        """
        Validate a JWT and return the pure claims.
        Only performs stateless validation (steps 1-8).
        """
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={"require": ["exp", "iat", "sub", "sid", "jti", "iss", "aud"]},
                leeway=datetime.timedelta(seconds=60),
            )
        except jwt.ExpiredSignatureError as e:
            raise AuthError("Token has expired.") from e
        except jwt.InvalidTokenError as e:
            raise AuthError("Invalid token.") from e

        # Explicitly check that 'iat' is not in the future (beyond leeway)
        # PyJWT handles exp, but iat validation is sometimes relaxed.
        now = datetime.datetime.now(datetime.UTC).timestamp()
        if payload.get("iat", 0) > now + 60:
            raise AuthError("Token issued in the future.")

        try:
            return TokenClaims(
                sub=uuid.UUID(payload["sub"]),
                sid=payload["sid"],
                jti=payload["jti"],
                iss=payload["iss"],
                aud=payload["aud"],
            )
        except (ValueError, KeyError, TypeError) as e:
            raise AuthError("Invalid token claims format.") from e
