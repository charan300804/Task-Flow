import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"
    DEAD_LETTER = "DEAD_LETTER"

class JobType(str, enum.Enum):
    GENERIC = "GENERIC"
    PYTHON_TASK = "PYTHON_TASK"
    ML_PREDICTION = "ML_PREDICTION"
    DATA_PROCESSING = "DATA_PROCESSING"

class WorkerStatus(str, enum.Enum):
    STARTING = "STARTING"
    IDLE = "IDLE"
    BUSY = "BUSY"
    UNHEALTHY = "UNHEALTHY"
    STOPPED = "STOPPED"
