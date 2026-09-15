"""
Role definitions.
"""

from enum import StrEnum


class Role(StrEnum):
    """System roles as defined in DRES."""

    PATIENT = "patient"
    HEALTH_WORKER = "health_worker"
    NURSE = "nurse"
    DOCTOR = "doctor"
    MEDICAL_OFFICER = "medical_officer"
    REVIEWER = "reviewer"
    ADMIN = "admin"
