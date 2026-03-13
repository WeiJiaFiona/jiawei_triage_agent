from pathlib import Path

from medical_agent.rule_engine import RuleEngine
from medical_agent.schemas import TriageRequest


def test_red_flag_chest_pain_rule():
    engine = RuleEngine(Path("configs/triage_rules.yaml"))
    req = TriageRequest.model_validate(
        {
            "patient_profile": {"patient_id": "P1", "age": 62, "sex": "male"},
            "chief_complaint": "chest pain with sweating",
            "vital_signs": {"temperature_c": 37.0, "spo2_percent": 95},
            "pain_score": 8,
            "special_population_tags": [],
        }
    )
    out = engine.evaluate(req)
    assert out.triage_floor == "red"
    assert out.must_transfer is True


def test_missing_temperature_triggers_followup():
    engine = RuleEngine(Path("configs/triage_rules.yaml"))
    req = TriageRequest.model_validate(
        {
            "patient_profile": {"patient_id": "P2", "age": 25, "sex": "female"},
            "chief_complaint": "cough",
            "vital_signs": {"heart_rate_bpm": 90},
            "pain_score": 2,
            "special_population_tags": [],
        }
    )
    out = engine.evaluate(req)
    assert "temperature_c" in out.missing_key_info
