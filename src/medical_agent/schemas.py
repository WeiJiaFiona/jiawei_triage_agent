from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import BaseModel, Field, model_validator


AcuityLevel = Literal["red", "yellow", "green"]


class PatientProfile(BaseModel):
    patient_id: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=120)
    sex: Literal["male", "female", "other"]


class VitalSigns(BaseModel):
    temperature_c: Optional[float] = Field(None, ge=30, le=45)
    heart_rate_bpm: Optional[int] = Field(None, ge=20, le=260)
    respiratory_rate_bpm: Optional[int] = Field(None, ge=4, le=80)
    blood_pressure_sys: Optional[int] = Field(None, ge=40, le=280)
    blood_pressure_dia: Optional[int] = Field(None, ge=20, le=180)
    spo2_percent: Optional[int] = Field(None, ge=40, le=100)


class TriageRequest(BaseModel):
    patient_profile: PatientProfile
    chief_complaint: str = Field(..., min_length=1)
    vital_signs: VitalSigns = Field(default_factory=VitalSigns)
    pain_score: Optional[int] = Field(None, ge=0, le=10)
    special_population_tags: List[str] = Field(default_factory=list)
    past_history_summary: Optional[str] = None
    allergy_summary: Optional[str] = None
    trauma_mechanism: Optional[str] = None


class EvidenceItem(BaseModel):
    source_type: Literal["rule", "guideline", "sop", "skill"]
    source_id: str
    snippet: str


class TriageHandoverSheet(BaseModel):
    patient_id: str
    triage_level: AcuityLevel
    risk_flags: List[str] = Field(default_factory=list)
    need_emergency_transfer: bool
    recommended_outpatient_entry: str
    need_human_override: bool
    temperature_c: Optional[float] = None
    chief_complaint_summary: str
    missing_key_info: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)


class TriageResponse(BaseModel):
    status: Literal["completed", "needs_more_info"]
    triage_handover_sheet: Optional[TriageHandoverSheet] = None
    follow_up_questions: List[str] = Field(default_factory=list)
    reasoning_summary: str

    @model_validator(mode="after")
    def validate_output(self) -> "TriageResponse":
        if self.status == "completed" and self.triage_handover_sheet is None:
            raise ValueError("triage_handover_sheet is required when status=completed")
        if self.status == "needs_more_info" and self.follow_up_questions == []:
            raise ValueError("follow_up_questions are required when status=needs_more_info")
        return self
