from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .config import AppConfig
from .schemas import TriageRequest


class LLMClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.enabled = bool(config.openai_api_key)
        self.client = None
        if self.enabled:
            self.client = OpenAI(
                api_key=config.openai_api_key,
                base_url=config.openai_base_url,
                timeout=config.openai_timeout_seconds,
            )

    def _heuristic(self, req: TriageRequest) -> dict[str, Any]:
        text = req.chief_complaint.lower()
        if any(k in text for k in ["chest pain", "胸痛", "呼吸困难", "意识"]):
            return {
                "triage_level": "red",
                "recommended_outpatient_entry": "emergency",
                "risk_flags": ["llm_emergency_pattern"],
                "confidence": 0.7,
            }
        if any(k in text for k in ["high fever", "高热", "acute abdominal pain", "腹痛"]):
            return {
                "triage_level": "yellow",
                "recommended_outpatient_entry": "emergency_observation",
                "risk_flags": ["llm_urgent_pattern"],
                "confidence": 0.6,
            }
        return {
            "triage_level": "green",
            "recommended_outpatient_entry": "general_outpatient",
            "risk_flags": [],
            "confidence": 0.6,
        }

    def propose_triage(self, req: TriageRequest, rule_hint: dict[str, Any], evidence: list[dict[str, str]]) -> dict[str, Any]:
        if not self.enabled:
            return self._heuristic(req)

        prompt = {
            "task": "triage",
            "constraints": [
                "no diagnosis",
                "no prescriptions",
                "must be safety-first",
                "output valid JSON only",
            ],
            "input": {
                "patient_profile": req.patient_profile.model_dump(),
                "chief_complaint": req.chief_complaint,
                "vital_signs": req.vital_signs.model_dump(),
                "pain_score": req.pain_score,
                "special_population_tags": req.special_population_tags,
                "rule_hint": rule_hint,
                "evidence": evidence,
            },
            "output_schema": {
                "triage_level": "red|yellow|green",
                "recommended_outpatient_entry": "string",
                "risk_flags": ["string"],
                "confidence": "0-1",
            },
        }

        try:
            completion = self.client.chat.completions.create(
                model=self.config.openai_model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical triage assistant. Safety first. Return only JSON.",
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
            )
            raw = completion.choices[0].message.content
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = self._heuristic(req)
                parsed["risk_flags"].append("llm_json_parse_fallback")
            return parsed
        except Exception:
            parsed = self._heuristic(req)
            parsed["risk_flags"].append("llm_api_fallback")
            return parsed
