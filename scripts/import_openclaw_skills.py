from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import selected OpenClaw SKILL.md files into local knowledge directory.")
    parser.add_argument("--openclaw-path", required=True, help="Path to OpenClaw-Medical-Skills/skills")
    parser.add_argument("--rag-config", default="configs/rag_sources.yaml", help="Path to rag_sources.yaml")
    parser.add_argument("--output-dir", default="data/knowledge/openclaw_skills", help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_root = Path(args.openclaw_path)
    rag_cfg = yaml.safe_load(Path(args.rag_config).read_text(encoding="utf-8"))
    include_skills = rag_cfg.get("include_skills", [])

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    missing = []
    for skill in include_skills:
        src = source_root / skill / "SKILL.md"
        if not src.exists():
            missing.append(skill)
            continue
        dst = out_dir / f"{skill}.md"
        shutil.copyfile(src, dst)
        copied += 1

    print(f"copied={copied}")
    if missing:
        print("missing=" + ",".join(missing))


if __name__ == "__main__":
    main()
