from __future__ import annotations

from dataclasses import dataclass

from supervisor.types.signal_dto import TaskSignal


@dataclass(frozen=True)
class RuntimeTruthBrief:
    headline: str
    details: list[str]

    def as_dict(self) -> dict[str, object]:
        return {"headline": self.headline, "details": list(self.details)}


class WilsonAgent:
    @staticmethod
    def render_report(signal: TaskSignal) -> str:
        if not isinstance(signal, TaskSignal):
            raise TypeError("signal must be a TaskSignal")

        return "\n".join(
            [
                "# Wilson Signal Report",
                "",
                f"- Task ID: {signal.task_id}",
                f"- Status: {signal.status}",
                "",
                "## Summary",
                signal.summary,
            ]
        )

    @staticmethod
    def summarize_runtime_truth(snapshot: dict) -> RuntimeTruthBrief:
        if not isinstance(snapshot, dict):
            raise TypeError("snapshot must be a dict")

        if not snapshot.get("ok"):
            return RuntimeTruthBrief(
                headline="Runtime truth unavailable.",
                details=[str(snapshot.get("error", "unknown error"))],
            )

        details: list[str] = []

        incident = next(iter(snapshot.get("incidents", [])), None)
        if incident:
            details.append(
                f"Oracle {incident['severity']} at {incident['stage']}: {incident['summary']}"
            )

        task = next(iter(snapshot.get("tasks", [])), None)
        if task:
            task_line = f"Latest task {task['id']} is {task['status']}: {task['summary']}"
            if task.get("session_persisted"):
                task_line += " Session persisted."
            details.append(task_line)

        event = next(iter(snapshot.get("events", [])), None)
        if event:
            event_bits = [f"Latest Gaia event {event['event_type']} by {event['actor']}."]
            if event.get("task_id"):
                event_bits.append(f"Task link: {event['task_id']}.")
            if event.get("target"):
                event_bits.append(f"Target: {event['target']}.")
            details.append(" ".join(event_bits))

        if not details:
            details.append("No recent Supervisor, Oracle, or Gaia rows were available.")

        headline = "Runtime truth is quiet."
        if incident:
            headline = f"Oracle has a {incident['severity']} incident in {incident['stage']}."
        elif task:
            headline = f"Latest Supervisor task {task['id']} is {task['status']}."
        elif event:
            headline = f"Latest Gaia event is {event['event_type']}."

        return RuntimeTruthBrief(headline=headline, details=details)
