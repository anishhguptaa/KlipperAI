import enum


class ProcessingStatus(str, enum.Enum):
    """Processing status enum for processing jobs"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
