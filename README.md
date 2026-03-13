# Triage Agent (Rules + RAG + Optional LLM)

## 1. 项目概览

当前分诊智能体提供以下能力：

- 红/黄/绿三色分诊
- 红旗征象与生命体征阈值规则兜底
- 基于本地知识库与可选 OpenClaw 技能文档的 RAG 检索
- 可选 LLM 推理（失败自动回退到本地启发式）
- 结构化分诊交接单输出（`triage_handover_sheet`）
- 命令行交互与 HTTP API 两种运行方式

## 2. 目录说明

- `configs/triage_rules.yaml`：分诊规则与红旗阈值
- `configs/departments_mapping.yaml`：科室映射规则
- `configs/rag_sources.yaml`：RAG 检索配置
- `scripts/triage_cli.py`：命令行分诊窗口
- `scripts/run_eval.py`：离线评测
- `scripts/run_multiturn_demo.py`：多轮场景演示
- `src/medical_agent/api.py`：API 服务
- `data/triage_cases.jsonl`：评测样例集

## 3. 环境准备

```bash
source ~/.bashrc >/dev/null 2>&1
conda activate ClassPass
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH

cd /home/jiawei2022/BME1325/medical_agent
pip install -r requirements.txt
```

## 4. 配置 `.env`

```bash
cp .env.example .env
```

常用配置：

- `OPENAI_API_KEY`：LLM 密钥（可为空）
- `OPENAI_BASE_URL`：OpenAI-compatible 接口地址
- `OPENAI_MODEL`：模型名
- `OPENCLAW_SKILLS_PATH`：OpenClaw skills 根目录（可选）
- `KNOWLEDGE_DIR`：本地知识库目录（会递归加载 `*.md`）

说明：

- 当 LLM 不可用时，系统会自动 fallback，不阻塞分诊流程。

## 5. 命令行分诊

启动：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src python scripts/triage_cli.py
```

交互规则：

- 按提示输入患者信息、主诉、体征
- 后续轮次可回车复用上一轮体征
- 输入 `/quit` 结束会话
- 输出包含：分诊等级、风险标签、是否转运、推荐去向

## 6. API 运行

启动：

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

离线评测：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src python scripts/run_eval.py
```

多轮演示：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src python scripts/run_multiturn_demo.py
```

单元测试：

```bash
cd /home/jiawei2022/BME1325/medical_agent
PYTHONPATH=./src pytest -q
```

## 8. OpenClaw 技能导入（可选）

```bash
cd /home/jiawei2022/BME1325/medical_agent
python scripts/import_openclaw_skills.py \
  --openclaw-path /path/to/OpenClaw-Medical-Skills/skills \
  --rag-config configs/rag_sources.yaml \
  --output-dir data/knowledge/openclaw_skills
```

## 9. 当前实现边界

- 当前实现目标是分诊与流程路由，不做最终临床诊断与处方。
- 医疗高风险场景必须人工复核。
