from __future__ import annotations

import json

from medical_agent.config import load_config
from medical_agent.schemas import TriageRequest
from medical_agent.triage_agent import TriageAgent


def run_turn(agent: TriageAgent, payload: dict) -> dict:
    req = TriageRequest.model_validate(payload)
    return agent.triage(req).model_dump()


def main() -> None:
    cfg = load_config()
    agent = TriageAgent(cfg)

    scenarios = [
        {
            "name": "scenario_missing_temp_then_complete",
            "turns": [
                {
                    "patient_profile": {"patient_id": "MT001", "age": 30, "sex": "female"},
                    "chief_complaint": "fever and cough for one day",
                    "vital_signs": {"heart_rate_bpm": 99, "respiratory_rate_bpm": 19, "blood_pressure_sys": 116, "blood_pressure_dia": 74, "spo2_percent": 98},
                    "pain_score": 3,
                    "special_population_tags": [],
                },
                {
                    "patient_profile": {"patient_id": "MT001", "age": 30, "sex": "female"},
                    "chief_complaint": "fever and cough for one day",
                    "vital_signs": {"temperature_c": 39.1, "heart_rate_bpm": 102, "respiratory_rate_bpm": 20, "blood_pressure_sys": 114, "blood_pressure_dia": 72, "spo2_percent": 97},
                    "pain_score": 4,
                    "special_population_tags": [],
                },
            ],
        },
        {
            "name": "scenario_escalate_to_critical",
            "turns": [
                {
                    "patient_profile": {"patient_id": "MT002", "age": 56, "sex": "male"},
                    "chief_complaint": "mild chest discomfort during exercise",
                    "vital_signs": {"temperature_c": 36.9, "heart_rate_bpm": 88, "respiratory_rate_bpm": 17, "blood_pressure_sys": 128, "blood_pressure_dia": 80, "spo2_percent": 98},
                    "pain_score": 3,
                    "special_population_tags": [],
                },
                {
                    "patient_profile": {"patient_id": "MT002", "age": 56, "sex": "male"},
                    "chief_complaint": "chest pain with sweating and near syncope",
                    "vital_signs": {"temperature_c": 37.2, "heart_rate_bpm": 118, "respiratory_rate_bpm": 24, "blood_pressure_sys": 92, "blood_pressure_dia": 58, "spo2_percent": 91},
                    "pain_score": 9,
                    "special_population_tags": [],
                },
            ],
        },
        {
            "name": "scenario_child_abdominal_boundary",
            "turns": [
                {
                    "patient_profile": {"patient_id": "MT003", "age": 7, "sex": "female"},
                    "chief_complaint": "abdominal pain since this morning",
                    "vital_signs": {"temperature_c": 37.4, "heart_rate_bpm": 97, "respiratory_rate_bpm": 20, "blood_pressure_sys": 102, "blood_pressure_dia": 64, "spo2_percent": 99},
                    "pain_score": 5,
                    "special_population_tags": ["child"],
                },
                {
                    "patient_profile": {"patient_id": "MT003", "age": 7, "sex": "female"},
                    "chief_complaint": "abdominal pain with high fever",
                    "vital_signs": {"temperature_c": 39.3, "heart_rate_bpm": 115, "respiratory_rate_bpm": 24, "blood_pressure_sys": 104, "blood_pressure_dia": 66, "spo2_percent": 98},
                    "pain_score": 6,
                    "special_population_tags": ["child"],
                },
            ],
        },
    ]

    for scenario in scenarios:
        print(f"\n=== {scenario['name']} ===")
        for i, turn in enumerate(scenario["turns"], start=1):
            out = run_turn(agent, turn)
            sheet = out.get("triage_handover_sheet")
            if sheet:
                print(json.dumps({
                    "turn": i,
                    "status": out["status"],
                    "triage_level": sheet["triage_level"],
                    "recommended_outpatient_entry": sheet["recommended_outpatient_entry"],
                    "risk_flags": sheet["risk_flags"],
                }, ensure_ascii=False))
            else:
                print(json.dumps({
                    "turn": i,
                    "status": out["status"],
                    "follow_up_questions": out.get("follow_up_questions", []),
                }, ensure_ascii=False))


if __name__ == "__main__":
    main()
