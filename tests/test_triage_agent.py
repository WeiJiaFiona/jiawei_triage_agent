from medical_agent.config import load_config
from medical_agent.schemas import TriageRequest
from medical_agent.triage_agent import TriageAgent


def test_child_abdominal_pain_routes_pediatrics():
    agent = TriageAgent(load_config())
    req = TriageRequest.model_validate(
        {
            "patient_profile": {"patient_id": "P3", "age": 7, "sex": "female"},
            "chief_complaint": "abdominal pain for 1 day",
            "vital_signs": {
                "temperature_c": 37.1,
                "heart_rate_bpm": 96,
                "respiratory_rate_bpm": 18,
                "blood_pressure_sys": 100,
                "blood_pressure_dia": 65,
                "spo2_percent": 99,
            },
            "pain_score": 4,
            "special_population_tags": ["child"],
        }
    )
    res = agent.triage(req)
    assert res.status == "completed"
    assert res.triage_handover_sheet is not None
    assert res.triage_handover_sheet.recommended_outpatient_entry == "pediatrics"
