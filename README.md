# Triage Agent (Rules + RAG + Optional LLM)

## 1. 项目说明

这是一个医疗分诊智能体，支持：

- 红/黄/绿分诊
- 红旗征象规则兜底
- RAG 检索知识增强
- 可选 LLM 推理（失败时自动 fallback 到规则/启发式）
- 结构化分诊交接单输出
- 命令行对话窗口与 HTTP API 两种使用方式

## 2. 核心能力

- 规则引擎：`configs/triage_rules.yaml`
- 科室映射：`configs/departments_mapping.yaml`
- RAG 配置：`configs/rag_sources.yaml`
- 命令行问诊：`scripts/triage_cli.py`
- 离线评测：`scripts/run_eval.py`
- 多轮演示：`scripts/run_multiturn_demo.py`
- API 服务：`src/medical_agent/api.py`

## 3. 环境准备

推荐使用你当前已有环境：

```bash
source ~/.bashrc >/dev/null 2>&1
conda activate ClassPass
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
```

安装依赖：

```bash
cd /home/jiawei2022/BME1325/medical_agent
pip install -r requirements.txt
```

## 4. 配置 `.env`

先复制模板：

```bash
cp .env.example .env
```

关键配置项：

- `OPENAI_API_KEY`：LLM 密钥（可为空）
- `OPENAI_BASE_URL`：OpenAI-compatible 接口地址（例如 `https://api.openai.com/v1`）
- `OPENAI_MODEL`：模型名
- `OPENCLAW_SKILLS_PATH`：OpenClaw skills 本地路径（可选）

说明：

- 若 LLM 不可用（额度不足/模型不支持/网络错误），系统会自动 fallback，不会阻塞分诊流程。

## 5. 命令行对话窗口（推荐）

启动：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src python scripts/triage_cli.py
```

使用方式：

- 按提示输入患者信息、主诉、体征
- 后续轮次可直接回车复用上一轮体征
- 输入 `/quit` 结束会话
- 终端输出结构化分诊结果（`triage_level`、`risk_flags`、`recommended_outpatient_entry` 等）

## 6. HTTP API 使用

启动服务：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src python -m medical_agent.main
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

分诊请求示例：

```bash
curl -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "patient_profile":{"patient_id":"P200","age":26,"sex":"female"},
    "chief_complaint":"high fever and cough since yesterday",
    "vital_signs":{"temperature_c":39.2,"heart_rate_bpm":103,"respiratory_rate_bpm":22,"blood_pressure_sys":112,"blood_pressure_dia":72,"spo2_percent":96},
    "pain_score":4,
    "special_population_tags":[]
  }'
```

## 7. 评测与测试

离线评测（样例集）：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src python scripts/run_eval.py
```

多轮场景演示：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src python scripts/run_multiturn_demo.py
```

单元测试：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src pytest -q
```

## 8. 导入 OpenClaw Skills（可选）

仅复用 `SKILL.md` 作为知识源，不依赖 open-claw runtime：

```bash
cd /home/jiawei2022/BME1325/medical_agent
python scripts/import_openclaw_skills.py \
  --openclaw-path /path/to/OpenClaw-Medical-Skills/skills \
  --rag-config configs/rag_sources.yaml \
  --output-dir data/knowledge/openclaw_skills
```

## 9. 注意事项

- 该项目用于分诊与流程模拟，不提供最终临床诊断或处方建议。
- 医疗高风险场景必须由人工医护复核。
