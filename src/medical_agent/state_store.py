from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionStore:
    sessions: dict[str, dict] = field(default_factory=dict)

    def upsert(self, patient_id: str, payload: dict) -> None:
        current = self.sessions.get(patient_id, {})
        current.update(payload)
        self.sessions[patient_id] = current

    def get(self, patient_id: str) -> dict:
        return self.sessions.get(patient_id, {})
