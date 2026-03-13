from __future__ import annotations

import json
from pathlib import Path

from medical_agent.config import load_config
from medical_agent.schemas import TriageRequest
from medical_agent.triage_agent import TriageAgent


def main() -> None:
    cfg = load_config()
    agent = TriageAgent(cfg)

    cases_path = Path("data/triage_cases.jsonl")
    total = 0
    passed = 0

    for line in cases_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        req = TriageRequest.model_validate(obj["input"])
        res = agent.triage(req)
        pred = res.triage_handover_sheet.triage_level if res.triage_handover_sheet else "needs_more_info"
        ok = pred == obj["expected_level"]
        total += 1
        passed += int(ok)
        print(f"[{ 'PASS' if ok else 'FAIL' }] {obj['name']} expected={obj['expected_level']} got={pred}")

    print(f"summary: {passed}/{total} passed")


if __name__ == "__main__":
    main()
