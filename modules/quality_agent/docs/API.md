# 文本审核 Agent 接口说明

## 1. 文本质量 Agent 查重检测接口

### 1.1 接口名称
- 文本查重分析（analyze_dedup）

### 1.2 功能描述
- 对新批次文本与历史文本进行批量查重，输出本批次内部高相似 pair 及与历史最相似 pair，支持大批量数据处理和历史向量缓存。

### 1.3 调用方式
- 本地 Python 函数/脚本调用
- 支持命令行批处理

### 1.4 输入参数
- `batch_path`：新批次文本的 JSON 文件路径（每条需有 `id` 和 `content` 字段）
- `history_path`：历史文本的 JSON 文件路径（同上）
- `output_path`：查重结果输出路径

### 1.5 输入样例
```json
[
  {"id": "1", "content": "这是第一条文本"},
  {"id": "2", "content": "这是第二条文本"}
]
```

### 1.6 输出结果
- `batch_high_sim_pairs`：本批次内部高相似 pair（如相似度 > 0.9）
- `batch_to_history`：每条新文本与历史最相似 pair

### 1.7 输出样例
```json
{
  "batch_high_sim_pairs": [
    {"batch_id1": "1", "batch_id2": "2", "duplicate_score": 0.92}
  ],
  "batch_to_history": [
    {"batch_id": "1", "most_similar_history_id": "10", "max_duplicate_score": 0.88}
  ]
}
```

### 1.8 主要流程
1. 加载本地 embedding 模型（如 bge-base-zh-v1.5）
2. 批量向量化新批次和历史文本
3. 计算余弦相似度，输出高相似 pair
4. 支持历史向量缓存，提升效率

### 1.9 依赖环境
- Python 3.8+
- 依赖包：sentence-transformers、numpy、scikit-learn 等

### 1.10 异常处理
- 输入文件格式错误、字段缺失时抛出异常并输出错误日志
- 向量化或模型加载失败时输出详细报错信息
- 输出路径不可写时终止并提示
