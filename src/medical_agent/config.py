from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    openai_timeout_seconds: int
    openclaw_skills_path: str | None
    triage_rules_path: Path
    departments_mapping_path: Path
    rag_sources_path: Path
    knowledge_dir: Path
    audit_log_path: Path



def load_config() -> AppConfig:
    load_dotenv()

    root = Path(__file__).resolve().parents[2]

    def resolve_path(env_key: str, default_rel: str) -> Path:
        value = os.getenv(env_key, default_rel)
        path = Path(value)
        if not path.is_absolute():
            path = root / path
        return path

    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        openai_timeout_seconds=int(os.getenv("OPENAI_TIMEOUT_SECONDS", "30")),
        openclaw_skills_path=os.getenv("OPENCLAW_SKILLS_PATH"),
        triage_rules_path=resolve_path("TRIAGE_RULES_PATH", "configs/triage_rules.yaml"),
        departments_mapping_path=resolve_path("DEPARTMENTS_MAPPING_PATH", "configs/departments_mapping.yaml"),
        rag_sources_path=resolve_path("RAG_SOURCES_PATH", "configs/rag_sources.yaml"),
        knowledge_dir=resolve_path("KNOWLEDGE_DIR", "data/knowledge"),
        audit_log_path=resolve_path("AUDIT_LOG_PATH", "data/audit/triage_audit.jsonl"),
    )
