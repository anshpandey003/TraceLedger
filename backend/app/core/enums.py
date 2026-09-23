from enum import StrEnum


class InvestigationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ClaimStatus(StrEnum):
    PENDING = "pending"
    INVESTIGATING = "investigating"
    COMPLETED = "completed"
    FAILED = "failed"


class Verdict(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"