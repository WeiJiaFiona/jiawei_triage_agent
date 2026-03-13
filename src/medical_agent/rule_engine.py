from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .schemas import TriageRequest


_SEVERITY = {"green": 0, "yellow": 1, "red": 2}


@dataclass
class RuleResult:
    triage_floor: str
    risk_flags: list[str]
    must_transfer: bool
    missing_key_info: list[str]
    evidence: list[tuple[str, str]]


class RuleEngine:
    def __init__(self, rules_path: Path):
        if not rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {rules_path}")
        self.rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))

    @staticmethod
    def _contains_any(text: str, patterns: list[str]) -> bool:
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    def evaluate(self, req: TriageRequest) -> RuleResult:
        text = " ".join(
            [
                req.chief_complaint,
                req.trauma_mechanism or "",
                req.past_history_summary or "",
                " ".join(req.special_population_tags),
            ]
        )

        triage_floor = "green"
        risk_flags: list[str] = []
        evidence: list[tuple[str, str]] = []

        required_fields = self.rules.get("required_fields", [])
        missing = []
        for key in required_fields:
            if key == "temperature_c" and req.vital_signs.temperature_c is None:
                missing.append("temperature_c")
            if key == "chief_complaint" and not req.chief_complaint.strip():
                missing.append("chief_complaint")

        for rf in self.rules.get("red_flags", []):
            if self._contains_any(text, rf.get("patterns", [])):
                risk_flags.append(rf["name"])
                triage_floor = "red"
                evidence.append((f"rule:{rf['name']}", rf.get("note", rf["name"])))

        vitals = req.vital_signs
        vt = self.rules.get("vital_thresholds", {})
        if vitals.spo2_percent is not None and vitals.spo2_percent < vt.get("spo2_low_red", 90):
            triage_floor = "red"
            risk_flags.append("low_spo2")
            evidence.append(("rule:vital_spo2", f"SpO2={vitals.spo2_percent}"))
        if vitals.blood_pressure_sys is not None and vitals.blood_pressure_sys < vt.get("sbp_low_red", 90):
            triage_floor = "red"
            risk_flags.append("hypotension")
            evidence.append(("rule:vital_sbp", f"SBP={vitals.blood_pressure_sys}"))
        if vitals.temperature_c is not None and vitals.temperature_c >= vt.get("temp_high_yellow", 39.0):
            if _SEVERITY[triage_floor] < _SEVERITY["yellow"]:
                triage_floor = "yellow"
            risk_flags.append("high_fever")
            evidence.append(("rule:vital_temp", f"Temp={vitals.temperature_c}"))

        boundary = self.rules.get("boundary_rules", {})
        abdominal_patterns = boundary.get("child_abdominal_pain_patterns", [])
        if req.patient_profile.age < 10 and self._contains_any(text, abdominal_patterns):
            risk_flags.append("child_abdominal_pain_boundary")
            evidence.append(("rule:boundary_peds", "Child abdominal pain should route to pediatrics"))

        must_transfer = triage_floor == "red"

        return RuleResult(
            triage_floor=triage_floor,
            risk_flags=sorted(set(risk_flags)),
            must_transfer=must_transfer,
            missing_key_info=sorted(set(missing)),
            evidence=evidence,
        )
