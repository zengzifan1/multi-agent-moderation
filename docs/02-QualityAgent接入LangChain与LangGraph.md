# QualityAgent 接入 LangChain / LangGraph（框架方案）

本节给出“最小改动可用”与“推荐重构可持续”两套方案，用于将仓库中的 `quality-agent/`（感知质量智能体）接入到 LangChain/LangGraph 的多智能体编排中。

> 目标：让质量智能体能够作为 Tool/Node 被合规智能体与整合器调用，并输出统一结构（QualitySignal），与其它智能体共享同一套 schema 与证据链。

---

## 0. 现状与接入难点（不深入细节）

- 当前 `quality-agent/` 更像“脚本/函数 + 文件路径 I/O”的工程形态（例如传入 `batch_path/history_path/output_path`）
- 目录名包含连字符 `quality-agent`，**不适合作为 Python import 包名**（推荐改为 `quality_agent` 或放入 `src/` 下的包）
- 部分功能依赖本地模型与缓存文件（例如 `.npy` 向量缓存），需要明确：是否要进入 GitHub、如何通过配置指定路径

这些点并不影响“能不能接入 LangChain”，但会影响：能否稳定复现、能否写测试、能否和其它 agent 共用同一进程与状态。

---

## 1. 方案 A（最小改动）：把现有能力当作黑盒 Tool

适用：你希望快速把质量智能体“挂进编排流程里”，先跑通端到端，不追求完美工程形态。

### A-1 约定一个输入/输出

- 输入：
  - `batch_path`（JSON，列表，每条含 `id`/`content`）
  - `history_path`（同上）
- 输出：
  - `quality_result.json`（你现有结构即可）

### A-2 在 LangChain 中包装成 Tool（思路）

- Tool 的实现只做三件事：
  1) 校验输入路径存在
  2) 调用 `analyze_dedup(batch_path, history_path, output_path)`
  3) 读取 output JSON 并作为 Tool 返回值

优点：几乎不动旧代码。
缺点：Tool 依赖文件系统；与其它 agent 的数据交互不够“内存化/结构化”。

---

## 2. 方案 B（推荐）：最小库化重构，使其自然接入 LangGraph

适用：你希望后续能写测试、能做 CI、能稳定复现，并与合规/协同 agent 共享统一 schema。

### B-1 把目录改成可 import 的包

推荐二选一：

- 方式 1（简单）：将 `quality-agent/` 重命名为 `quality_agent/`，并在根目录增加 `quality_agent/__init__.py`
- 方式 2（更规范）：建立 `src/multi_agent_moderation/quality_agent/`，把核心逻辑迁进去（更利于打包与 CI）

### B-2 抽一个稳定的“质量智能体 API”

建议新增一个薄封装（例如 `quality_agent/api.py`），提供：

- `QualityAgent` 类（建议缓存模型实例，避免每次加载）
- `dedup(batch_items, history_items) -> QualitySignal`（内存结构输入输出）
- 可选保留：`dedup_from_paths(batch_path, history_path) -> QualitySignal`（兼容旧脚本）

### B-3 统一输出结构（QualitySignal）

建议质量智能体至少输出这些字段（用于与合规/整合对齐）：

- `quality_risk_level`: `low|medium|high`（或数值分级）
- `duplicate`: 
  - `batch_high_sim_pairs`: [{id1,id2,score}]
  - `batch_to_history_top1`: [{id, history_id, score}]
- `evidence`: 可追溯证据（命中对、阈值、模型版本/特征版本）

> 这部分最终应落到全局 schema（Pydantic），而不是散落在脚本里。

---

## 3. 在 LangChain / LangGraph 中如何“连接”质量智能体

### 3.1 LangChain Tool（推荐形态）

- 将 `QualityAgent.dedup(...)` 包装为 Tool
- Tool 入参使用结构化对象（dict / Pydantic）而不是文件路径

### 3.2 LangGraph Node（推荐形态）

- 状态里持有：`items`、`history`、`quality_signal`、`compliance_signal`、`final_decision`
- 一个 node 负责调用质量智能体，把结果写入 `state.quality_signal`
- 合规 node 与质量 node 可并行；整合 node 负责路由：合规优先、不确定→复核

---

## 6. 参考实现（已落地）

本仓库已提供最小 LangGraph 编排实现：

- 代码位置：`src/multi_agent_moderation/chains/langgraph_orchestrator.py`
- Demo：`src/multi_agent_moderation/examples/run_langgraph_demo.py`

运行示例（需安装 langgraph）：

```bash
pip install langgraph
python -m multi_agent_moderation.examples.run_langgraph_demo
```

---

## 4. 建议的仓库层面配套（避免踩坑）

- **大文件/模型不要直接进 Git**：
  - `models/`（bge 权重）建议改为“下载说明 + 可配置路径”，必要时用 Git LFS
  - `*.npy`（向量缓存）建议默认忽略
- requirements：如果某模块用到 `pandas`，确保在 `requirements.txt` 或未来的 `pyproject.toml` 里声明

---

## 5. 推荐落地顺序（最省心）

1) 先用方案 A 跑通“质量工具能被调用”
2) 再逐步做方案 B：改包名 + 抽 `QualityAgent` + 内存化 API
3) 最后再接入合规与协同 agent（LangGraph 编排 + 统一 schema + 证据链）
