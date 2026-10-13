
from dataclasses import dataclass


@dataclass
class TaskMessage:
    task_id: int
    x: int
    y: int
    operation: str = "sum"


@dataclass
class ResultMessage:
    task_id: int
    worker_id: str
    x: int
    y: int
    result: int
