from __future__ import annotations

import json
from typing import Optional

from medical_agent.config import load_config
from medical_agent.schemas import TriageRequest
from medical_agent.triage_agent import TriageAgent


def _read_str(prompt: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default not in (None, "") else ""
    value = input(f"{prompt}{suffix}: ").strip()
    if value == "" and default is not None:
        return default
    return value


def _read_int(prompt: str, default: Optional[int] = None) -> Optional[int]:
    while True:
        raw = _read_str(prompt, str(default) if default is not None else None)
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print("请输入整数，或直接回车跳过。")


def _read_float(prompt: str, default: Optional[float] = None) -> Optional[float]:
    while True:
        raw = _read_str(prompt, str(default) if default is not None else None)
        if raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            print("请输入数字，或直接回车跳过。")


def _read_tags(default: Optional[list] = None) -> list:
    current = ",".join(default or [])
    raw = _read_str("特殊人群标签(逗号分隔，如 child,immunocompromised)", current)
    if raw.strip() == "":
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def run_cli() -> None:
    cfg = load_config()
    agent = TriageAgent(cfg)

    print("=== Triage Agent CLI ===")
    print("输入 /quit 退出。第一轮请尽量填写完整体征；后续轮次可回车沿用上一轮。\n")

    patient_id = _read_str("Patient ID")
    age = _read_int("年龄")
    sex = _read_str("性别(male/female/other)", "male")

    last = {
        "temperature_c": None,
        "heart_rate_bpm": None,
        "respiratory_rate_bpm": None,
        "blood_pressure_sys": None,
        "blood_pressure_dia": None,
        "spo2_percent": None,
        "pain_score": None,
        "special_population_tags": [],
    }

    turn = 1
    while True:
        print(f"\n--- 第 {turn} 轮 ---")
        chief = _read_str("主诉")
        if chief.lower() == "/quit":
            print("已退出。")
            break

        temp = _read_float("体温(°C)", last["temperature_c"])
        hr = _read_int("心率(bpm)", last["heart_rate_bpm"])
        rr = _read_int("呼吸频率(bpm)", last["respiratory_rate_bpm"])
        sbp = _read_int("收缩压(mmHg)", last["blood_pressure_sys"])
        dbp = _read_int("舒张压(mmHg)", last["blood_pressure_dia"])
        spo2 = _read_int("血氧(%)", last["spo2_percent"])
        pain = _read_int("疼痛评分(0-10)", last["pain_score"])
        tags = _read_tags(last["special_population_tags"])

        payload = {
            "patient_profile": {
                "patient_id": patient_id,
                "age": age,
                "sex": sex,
            },
            "chief_complaint": chief,
            "vital_signs": {
                "temperature_c": temp,
                "heart_rate_bpm": hr,
                "respiratory_rate_bpm": rr,
                "blood_pressure_sys": sbp,
                "blood_pressure_dia": dbp,
                "spo2_percent": spo2,
            },
            "pain_score": pain,
            "special_population_tags": tags,
        }

        req = TriageRequest.model_validate(payload)
        res = agent.triage(req).model_dump()

        print("\n[分诊输出]")
        if res["status"] == "needs_more_info":
            print(json.dumps({
                "status": res["status"],
                "follow_up_questions": res.get("follow_up_questions", []),
                "reasoning_summary": res.get("reasoning_summary", ""),
            }, ensure_ascii=False, indent=2))
        else:
            sheet = res["triage_handover_sheet"]
            print(json.dumps({
                "status": res["status"],
                "triage_level": sheet["triage_level"],
                "recommended_outpatient_entry": sheet["recommended_outpatient_entry"],
                "need_emergency_transfer": sheet["need_emergency_transfer"],
                "need_human_override": sheet["need_human_override"],
                "risk_flags": sheet["risk_flags"],
                "missing_key_info": sheet["missing_key_info"],
            }, ensure_ascii=False, indent=2))

        last.update(
            {
                "temperature_c": temp,
                "heart_rate_bpm": hr,
                "respiratory_rate_bpm": rr,
                "blood_pressure_sys": sbp,
                "blood_pressure_dia": dbp,
                "spo2_percent": spo2,
                "pain_score": pain,
                "special_population_tags": tags,
            }
        )
        turn += 1


if __name__ == "__main__":
    run_cli()
