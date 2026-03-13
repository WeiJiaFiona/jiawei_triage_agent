from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-\u4e00-\u9fff]+")


@dataclass
class RetrievalItem:
    source_type: str
    source_id: str
    text: str


@dataclass
class RetrievalResult:
    source_type: str
    source_id: str
    snippet: str
    score: float


class SimpleRAGRetriever:
    def __init__(self, knowledge_dir: Path, rag_sources_path: Path, openclaw_skills_path: str | None = None):
        self.knowledge_dir = knowledge_dir
        self.rag_sources = yaml.safe_load(rag_sources_path.read_text(encoding="utf-8"))
        self.openclaw_skills_path = Path(openclaw_skills_path) if openclaw_skills_path else None
        self.items = self._load_items()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t.lower() for t in _TOKEN_RE.findall(text)]

    def _load_items(self) -> list[RetrievalItem]:
        items: list[RetrievalItem] = []

        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        for file in sorted(self.knowledge_dir.rglob("*.md")):
            text = file.read_text(encoding="utf-8", errors="ignore")
            if text.strip():
                items.append(RetrievalItem("guideline", str(file), text))

        use_openclaw = bool(self.rag_sources.get("use_openclaw_skills", True))
        include_skills = set(self.rag_sources.get("include_skills", []))
        if use_openclaw and self.openclaw_skills_path and self.openclaw_skills_path.exists():
            for skill_name in sorted(include_skills):
                skill_file = self.openclaw_skills_path / skill_name / "SKILL.md"
                if skill_file.exists():
                    text = skill_file.read_text(encoding="utf-8", errors="ignore")
                    items.append(RetrievalItem("skill", f"openclaw:{skill_name}", text))

        return items

    def search(self, query: str, top_k: int = 5, min_relevance_score: float = 0.72) -> list[RetrievalResult]:
        if not self.items:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []
        q_set = set(q_tokens)

        scored: list[RetrievalResult] = []
        for item in self.items:
            t_tokens = self._tokenize(item.text)
            if not t_tokens:
                continue
            overlap = len(q_set.intersection(set(t_tokens)))
            if overlap == 0:
                continue
            score = overlap / math.sqrt(len(set(t_tokens)))
            if score >= min_relevance_score:
                snippet = item.text[:320].replace("\n", " ")
                scored.append(
                    RetrievalResult(
                        source_type=item.source_type,
                        source_id=item.source_id,
                        snippet=snippet,
                        score=score,
                    )
                )

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]
