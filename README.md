# 多智能体文本内容审核系统

面向内容平台的风控与质量治理，本项目提供可复现的多智能体审核流程、结构化输出与可追溯证据链，适用于企业内容安全、社区治理与营销合规等场景。实现成果后续整理为论文材料，本仓库以工程实现与可复现流程为主。

## 适用场景

- 社区内容治理：低质/灌水/重复内容识别与分层处置
- 营销合规：导流与隐晦违规识别、证据链留痕
- 企业内容安全：规则约束、审计留痕与人工复核协作

## 核心能力

- 多智能体分工：质量 / 合规 / 复核
- 风险路由：合规优先，不确定进入复核
- 结构化结果：统一字段口径，便于系统集成
- 证据链：命中片段、引用来源与审计留痕

## 工作流

1. 输入文本与元信息
2. 合规判定（规则 + 语义）
3. 质量评估（相似度/重复检测）
4. 结果融合与处置路由
5. 审计留痕与复核载荷生成

## 架构与模块

- 编排层：统一流程入口与路由决策
- 质量智能体：语义相似度检索与重复检测
- 合规智能体：规则命中 + 语义判别 + 证据引用
- 复核智能体：复核载荷与替换建议

## 关键输出（结构化结果）

```json
{
	"item_id": "demo-1",
	"final_action": "review",
	"quality": {
		"risk_level": "medium",
		"duplicate_score": 0.82,
		"evidence": {
			"mode": "in_memory",
			"batch_high_sim_pairs": [],
			"batch_to_history": []
		}
	},
	"compliance": {
		"risk_level": "medium",
		"labels": ["marketing"],
		"evidence": {
			"spans": [],
			"references": [],
			"action_hint": "review",
			"evidence_complete": true,
			"hit_count": 1,
			"versions": {"rules": "a1b2c3d4", "knowledge_base": "e5f6g7h8"}
		}
	},
	"review": {
		"need_review": true,
		"reason": "rule: compliance or quality indicates risk",
		"action": "review",
		"review_payload": {},
		"decision_basis": {},
		"trace": {}
	}
}
```

## 快速开始

```bash
pip install -r requirements.txt
python -m multi_agent_moderation.examples.run_demo
```

可选 LangGraph 编排：

```bash
pip install langgraph
python -m multi_agent_moderation.examples.run_langgraph_demo
```

## 使用与配置

- 配置模板：[config.example.yaml](config.example.yaml)，配合 `MAM_CONFIG_PATH` 与 `MAM_PROFILE` 使用
- 环境变量：见 [.env.example](.env.example)
- 统一输出与落盘：`multi_agent_moderation.pipeline`

常用环境变量：

- `MAM_OUTPUT_DIR`：输出目录
- `MAM_AUDIT_LOG_PATH`：审计日志 JSONL 路径
- `MAM_AUDIT_DB_PATH`：审计数据库路径
- `MAM_COMPLIANCE_RULES_PATH` / `MAM_COMPLIANCE_KB_PATH`
- `MAM_REVIEW_REPLACEMENT_RULES_PATH`
- `MAM_QUALITY_OUTPUT_PATH`
- `QUALITY_AGENT_MODEL_DIR`

## 服务化与队列（可选）

```bash
uvicorn multi_agent_moderation.service.app:app --host 0.0.0.0 --port 8000
```

异步批量：`/moderate/async`，结果查询：`/jobs/{job_id}`

## 统一编排入口

```python
from multi_agent_moderation.pipeline import run_item_dict
from multi_agent_moderation.schemas import ModerationItem

item = ModerationItem(item_id="demo-1", content="This is the best deal, totally free.")
result = run_item_dict(item)
print(result)
```

## 模块文档

- 质量模块文档：[modules/quality_agent/docs/README.md](modules/quality_agent/docs/README.md)
- 合规模块文档：[modules/compliance_agent/docs/README.md](modules/compliance_agent/docs/README.md)
- 复核模块文档：[modules/review_agent/docs/README.md](modules/review_agent/docs/README.md)

## Docs

- Overview and API: [docs/INDEX.md](docs/INDEX.md)

## 目录结构

```
multi-agent-moderation/
├── src/multi_agent_moderation/     # 编排、工具、服务化
├── modules/                        # 三类智能体模块
├── tests/                          # 基础测试
├── config.example.yaml             # 配置模板
├── .env.example                    # 环境变量模板
└── requirements.txt
```

## 安全说明

示例数据为人工构造脱敏样本，不包含真实业务数据或密钥。

## License

MIT License，见 LICENSE。
