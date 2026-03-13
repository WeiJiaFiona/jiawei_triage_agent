# Triage Agent (ChatGPT + Rules + RAG)

## What is implemented

- ChatGPT API as LLM layer
- Rule engine safety floor (red/yellow/green)
- RAG retrieval over local knowledge and selected OpenClaw skills
- Structured triage handover output
- FastAPI endpoints (`/health`, `/triage`)
- Basic tests and offline evaluation script

## Quick start

```bash
cd medical_agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Import OpenClaw skills (without OpenClaw framework)

```bash
python scripts/import_openclaw_skills.py \
  --openclaw-path /path/to/OpenClaw-Medical-Skills/skills \
  --rag-config configs/rag_sources.yaml \
  --output-dir data/knowledge/openclaw_skills
```

## Run API

```bash
PYTHONPATH=./src python -m medical_agent.main
```

## Run tests

```bash
PYTHONPATH=./src pytest -q
```

## Run offline eval

```bash
PYTHONPATH=./src python scripts/run_eval.py
```
