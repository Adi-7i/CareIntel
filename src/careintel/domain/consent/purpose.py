"""
Consent Purpose enum.
"""

from enum import StrEnum


class ConsentPurpose(StrEnum):
    """
    Purposes for which consent is gathered.
    """

    DATA_PROCESSING = "data_processing"
    AI_ANALYSIS = "ai_analysis"
    EXPORT = "export"
    REFERRAL = "referral"
