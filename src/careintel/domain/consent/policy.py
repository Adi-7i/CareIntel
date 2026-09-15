"""
Consent policy.
"""

from __future__ import annotations

import uuid

from careintel.core.errors import ConsentError
from careintel.domain.consent.models import ConsentContext
from careintel.domain.consent.purpose import ConsentPurpose


class ConsentPolicy:
    """
    Central consent policy evaluator.
    """

    @staticmethod
    def require_active(
        consent: ConsentContext | None,
        subject_id: uuid.UUID,
        purpose: str | ConsentPurpose,
        required_notice_version: str,
    ) -> ConsentContext:
        """
        Require that the provided consent context is active and valid for the given
        subject, purpose, and version.

        Raises ConsentError (HTTP 403) if requirements are not met.
        """
        purpose_str = str(purpose)

        if consent is None:
            raise ConsentError(f"No active consent found for purpose '{purpose_str}'.")

        if consent.subject_id != subject_id:
            raise ConsentError("Consent subject does not match the requested subject.")

        if consent.purpose != purpose_str:
            raise ConsentError(f"Consent purpose mismatch. Expected '{purpose_str}'.")

        if consent.state != "ACTIVE":
            raise ConsentError("Consent is not in ACTIVE state.")

        if consent.notice_version != required_notice_version:
            raise ConsentError("Consent notice version mismatch or stale.")

        return consent
