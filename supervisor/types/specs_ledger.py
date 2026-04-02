from __future__ import annotations

from dataclasses import dataclass, field, replace


ALLOWED_TASK_STATUSES = {
    "pending",
    "in_progress",
    "done",
    "blocked",
    "failed",
    "cancelled",
}


def _normalize_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    return normalized


def _normalize_lines(values: list[str], field_name: str) -> list[str]:
    if not isinstance(values, list):
        raise TypeError(f"{field_name} must be a list of strings")

    normalized: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise TypeError(f"{field_name}[{index}] must be a string")
        line = " ".join(value.split())
        if not line:
            raise ValueError(f"{field_name}[{index}] must not be empty")
        normalized.append(line)

    return normalized


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    description: str
    constraints: list[str]
    acceptance_criteria: list[str]
    status: str = "pending"

    def __post_init__(self) -> None:
        object.__setattr__(self, "task_id", _normalize_text(self.task_id, "task_id"))
        object.__setattr__(self, "description", _normalize_text(self.description, "description"))
        object.__setattr__(self, "constraints", _normalize_lines(self.constraints, "constraints"))
        object.__setattr__(
            self,
            "acceptance_criteria",
            _normalize_lines(self.acceptance_criteria, "acceptance_criteria"),
        )

        normalized_status = _normalize_text(self.status, "status")
        if normalized_status not in ALLOWED_TASK_STATUSES:
            raise ValueError(f"status must be one of {sorted(ALLOWED_TASK_STATUSES)}")
        object.__setattr__(self, "status", normalized_status)


@dataclass
class SpecsLedger:
    _tasks: dict[str, TaskSpec] = field(default_factory=dict, init=False, repr=False)

    def add_task(self, spec: TaskSpec) -> None:
        if not isinstance(spec, TaskSpec):
            raise TypeError("spec must be a TaskSpec")
        if spec.task_id in self._tasks:
            raise ValueError(f"task_id already exists: {spec.task_id}")
        self._tasks[spec.task_id] = self._copy_spec(spec)

    def get_pending_tasks(self) -> list[TaskSpec]:
        pending_specs = [spec for spec in self._tasks.values() if spec.status == "pending"]
        return [self._copy_spec(spec) for spec in pending_specs]

    def mark_task_status(self, task_id: str, new_status: str) -> None:
        normalized_task_id = _normalize_text(task_id, "task_id")
        normalized_status = _normalize_text(new_status, "new_status")
        if normalized_status not in ALLOWED_TASK_STATUSES:
            raise ValueError(f"new_status must be one of {sorted(ALLOWED_TASK_STATUSES)}")

        current_spec = self._tasks.get(normalized_task_id)
        if current_spec is None:
            raise KeyError(f"unknown task_id: {normalized_task_id}")

        self._tasks[normalized_task_id] = replace(current_spec, status=normalized_status)

    def get_task_prompt_context(self, task_id: str) -> str:
        normalized_task_id = _normalize_text(task_id, "task_id")
        spec = self._tasks.get(normalized_task_id)
        if spec is None:
            raise KeyError(f"unknown task_id: {normalized_task_id}")

        constraints_lines = "\n".join(f"- {constraint}" for constraint in spec.constraints)
        acceptance_lines = "\n".join(f"- {criterion}" for criterion in spec.acceptance_criteria)

        return "\n".join(
            [
                f"Task ID: {spec.task_id}",
                f"Status: {spec.status}",
                "Description:",
                spec.description,
                "Constraints:",
                constraints_lines,
                "Acceptance Criteria:",
                acceptance_lines,
            ]
        )

    @staticmethod
    def _copy_spec(spec: TaskSpec) -> TaskSpec:
        return TaskSpec(
            task_id=spec.task_id,
            description=spec.description,
            constraints=list(spec.constraints),
            acceptance_criteria=list(spec.acceptance_criteria),
            status=spec.status,
        )
