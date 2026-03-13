from __future__ import annotations

from dataclasses import dataclass

import yaml

from .audit_logger import AuditLogger
from .config import AppConfig
from .llm_client import LLMClient
from .rag_retriever import SimpleRAGRetriever
from .rule_engine import RuleEngine
from .schemas import EvidenceItem, TriageHandoverSheet, TriageRequest, TriageResponse
from .state_store import SessionStore

_SEVERITY = {"green": 0, "yellow": 1, "red": 2}


@dataclass
class DepartmentMapper:
    mapping: dict

    @classmethod
    def load(cls, mapping_path):
        data = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
        return cls(mapping=data)

    def map_department(self, req: TriageRequest, triage_level: str) -> str:
        complaint = req.chief_complaint.lower()

        if triage_level == "red":
            return "emergency_resuscitation"
        if req.patient_profile.age < 10 and any(k in complaint for k in ["abdominal", "腹痛", "belly"]):
            return "pediatrics"

        rules = self.mapping.get("keyword_routing", {})
        for dept, keywords in rules.items():
            if any(k.lower() in complaint for k in keywords):
                return dept

        return self.mapping.get("default_department", "general_outpatient")


class TriageAgent:
    def __init__(self, config: AppConfig):
        self.config = config
        self.rule_engine = RuleEngine(config.triage_rules_path)
        self.mapper = DepartmentMapper.load(config.departments_mapping_path)
        self.retriever = SimpleRAGRetriever(
            knowledge_dir=config.knowledge_dir,
            rag_sources_path=config.rag_sources_path,
            openclaw_skills_path=config.openclaw_skills_path,
        )
        self.llm = LLMClient(config)
        self.session_store = SessionStore()
        self.audit_logger = AuditLogger(config.audit_log_path)

    @staticmethod
    def _max_level(a: str, b: str) -> str:
        return a if _SEVERITY[a] >= _SEVERITY[b] else b

    def triage(self, req: TriageRequest) -> TriageResponse:
        rule = self.rule_engine.evaluate(req)

        emergency_by_rule = rule.must_transfer
        if rule.missing_key_info and not emergency_by_rule:
            follow_ups = []
            for field in rule.missing_key_info:
                if field == "temperature_c":
                    follow_ups.append("请提供当前体温（摄氏度）。")
                elif field == "chief_complaint":
                    follow_ups.append("请描述本次最主要不适症状。")
            response = TriageResponse(
                status="needs_more_info",
                follow_up_questions=follow_ups,
                reasoning_summary="Missing required fields before safe triage.",
            )
            self.audit_logger.log(
                {
                    "event": "TRIAGE_NEEDS_MORE_INFO",
                    "patient_id": req.patient_profile.patient_id,
                    "missing_key_info": rule.missing_key_info,
                }
            )
            return response

        query = " ".join([req.chief_complaint, req.past_history_summary or "", " ".join(rule.risk_flags)])
        rag_cfg = yaml.safe_load(self.config.rag_sources_path.read_text(encoding="utf-8"))
        rag_results = self.retriever.search(
            query=query,
            top_k=int(rag_cfg.get("top_k", 5)),
            min_relevance_score=float(rag_cfg.get("min_relevance_score", 0.72)),
        )

        rag_evidence = [
            {"source_type": r.source_type, "source_id": r.source_id, "snippet": r.snippet} for r in rag_results
        ]

        llm_proposal = self.llm.propose_triage(
            req=req,
            rule_hint={
                "triage_floor": rule.triage_floor,
                "risk_flags": rule.risk_flags,
                "must_transfer": rule.must_transfer,
            },
            evidence=rag_evidence,
        )

        llm_level = llm_proposal.get("triage_level", "green")
        if llm_level not in _SEVERITY:
            llm_level = "green"

        final_level = self._max_level(llm_level, rule.triage_floor)
        need_transfer = final_level == "red" or rule.must_transfer

        combined_flags = sorted(set(rule.risk_flags + llm_proposal.get("risk_flags", [])))
        confidence = float(llm_proposal.get("confidence", 0.5))
        retrieval_confident = len(rag_results) > 0
        need_human_override = confidence < 0.6 or not retrieval_confident

        recommended = llm_proposal.get("recommended_outpatient_entry")
        if not recommended:
            recommended = self.mapper.map_department(req, final_level)
        complaint_lower = req.chief_complaint.lower()
        if req.patient_profile.age < 10 and any(k in complaint_lower for k in ["abdominal", "腹痛", "belly"]):
            recommended = "pediatrics"
        if final_level == "red":
            recommended = "emergency_resuscitation"

        evidence = [
            EvidenceItem(source_type="rule", source_id=eid, snippet=msg) for eid, msg in rule.evidence
        ]
        evidence.extend(
            [
                EvidenceItem(
                    source_type=("skill" if r.source_type == "skill" else "guideline"),
                    source_id=r.source_id,
                    snippet=r.snippet,
                )
                for r in rag_results
            ]
        )

        handover = TriageHandoverSheet(
            patient_id=req.patient_profile.patient_id,
            triage_level=final_level,
            risk_flags=combined_flags,
            need_emergency_transfer=need_transfer,
            recommended_outpatient_entry=recommended,
            need_human_override=need_human_override,
            temperature_c=req.vital_signs.temperature_c,
            chief_complaint_summary=req.chief_complaint[:240],
            missing_key_info=rule.missing_key_info,
            evidence=evidence,
        )

        self.session_store.upsert(
            req.patient_profile.patient_id,
            {
                "chief_complaint": req.chief_complaint,
                "triage_level": final_level,
                "risk_flags": combined_flags,
                "need_emergency_transfer": need_transfer,
                "recommended_outpatient_entry": recommended,
            },
        )
        self.audit_logger.log(
            {
                "event": "TRIAGE_COMPLETED",
                "patient_id": req.patient_profile.patient_id,
                "triage_level": final_level,
                "risk_flags": combined_flags,
                "rule_floor": rule.triage_floor,
                "llm_level": llm_level,
                "need_human_override": need_human_override,
                "evidence_count": len(evidence),
            }
        )

        return TriageResponse(
            status="completed",
            triage_handover_sheet=handover,
            reasoning_summary="Rule engine constrained LLM output with evidence-grounded retrieval.",
        )
