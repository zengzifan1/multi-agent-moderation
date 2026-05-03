# 多智能体社交媒体文本内容审核系统

本项目是毕业论文《基于多智能体的社交媒体文本内容审核系统设计与实现》的开源实现载体，面向“文本内容审核”的工程落地：通过多智能体协作完成风险识别、分层处置与可追溯证据输出，并支持不确定样本进入人工复核。

## 设计要点

- 多智能体拆分：质量智能体 / 合规智能体 / 人机协同
- 分层处置与安全路由：合规优先；不确定或冲突结果进入复核
- 结构化输出：统一输入/输出字段口径，便于系统集成与测试
- 可追溯证据链：保留命中片段、依据来源与审计信息

## 工作流概览

1. 输入文本与必要元信息
2. 合规智能体给出违规类型、依据与建议动作
3. 质量智能体给出相似/重复等质量信号与证据
4. 结果整合：合规优先、质量参考；不确定进入复核
5. 留痕：记录结果、证据与裁决（用于审计与复盘）

## 文档

- 项目概览：docs/00-项目概览.md
- 技术选型（Coze → 本地开源）：docs/01-技术选型.md
- QualityAgent 接入（LangChain/LangGraph）：docs/02-QualityAgent接入LangChain与LangGraph.md
- 质量模块文档：modules/quality_agent/docs/README.md
- 合规模块文档：modules/compliance_agent/docs/README.md
- 复核模块文档：modules/review_agent/docs/README.md

## 快速开始（集中说明）

### 1) 安装依赖

```bash
pip install -r requirements.txt
```

### 2) 运行最小流程

```bash
python -m multi_agent_moderation.examples.run_demo
```

### 3) 使用 LangGraph 编排（可选）

```bash
pip install langgraph
python -m multi_agent_moderation.examples.run_langgraph_demo
```

## 可复现与工程化说明（简要）

- src 层通过 tools 动态加载 modules 目录，便于保持模块独立演进。
- 质量模块默认读取 modules/quality_agent/data 中的 JSON，并将结果写入 outputs；可通过 `ModerationItem.meta` 传入 `batch_path/history_path/output_path` 覆盖。
- 统一输出与落盘入口在 `multi_agent_moderation.pipeline` 与 `multi_agent_moderation.tools`。

## 生产级工程化细节（简要）

- 环境变量：`MAM_OUTPUT_DIR`、`MAM_AUDIT_LOG_PATH`、`MAM_COMPLIANCE_RULES_PATH`、`MAM_COMPLIANCE_KB_PATH`、`MAM_REVIEW_REPLACEMENT_RULES_PATH`、`MAM_QUALITY_OUTPUT_PATH`
- 审计落盘：使用 `pipeline.run_item_and_audit` / `run_batch_and_audit` 输出 JSONL
- 模型路径：质量模块依赖本地模型目录，可通过 `QUALITY_AGENT_MODEL_DIR` 配置
- 服务化（可选）：`uvicorn multi_agent_moderation.service.app:app --host 0.0.0.0 --port 8000`
- 任务队列（可选）：`/moderate/async` + `/jobs/{job_id}` 使用内置轻量队列

## 代码结构（专业化布局）

- src/multi_agent_moderation/: 核心编排与工具封装
- modules/quality_agent/: 现有质量智能体实现（独立模块，后续通过 tools 适配）
- modules/compliance_agent/: 合规智能体实现（规则优先，可扩展 RAG/LLM）
- modules/review_agent/: 人机协同与复核路由实现

## 安全与合规

- 本项目不包含任何真实业务数据、敏感样本或密钥。
- 示例与演示数据仅使用人工构造的脱敏文本。

## License

MIT License，见 LICENSE。
