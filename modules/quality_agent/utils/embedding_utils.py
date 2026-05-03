# 加载本地embedding模型（只加载一次，节省内存和时间）
# 路径为本地已下载的bge-base-zh-v1.5模型文件夹
from sentence_transformers import SentenceTransformer
import os
import hashlib
import numpy as np

# 加载本地embedding模型
def load_model():
    default_path = os.path.join(os.path.dirname(__file__), "..", "models", "bge-base-zh-v1.5")
    model_path = os.environ.get("QUALITY_AGENT_MODEL_DIR", default_path)
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            "Model files not found. Set QUALITY_AGENT_MODEL_DIR or download "
            "the model into modules/quality_agent/models/bge-base-zh-v1.5."
        )
    return SentenceTransformer(model_path)

# 批量向量化
def batch_vectorize(model, batch_texts, history_texts, batch_size=32):
    batch_embs = model.encode(batch_texts, show_progress_bar=True, batch_size=batch_size)
    history_embs = model.encode(history_texts, show_progress_bar=True, batch_size=batch_size)
    return batch_embs, history_embs 

# 计算文件内容的SHA256哈希
def calc_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            buf = f.read(8192)
            if not buf:
                break
            hasher.update(buf)
    return hasher.hexdigest()

# 保存向量为npy文件
def save_embeddings_npy(embeddings, npy_path):
    np.save(npy_path, embeddings)

# 加载npy向量
def load_embeddings_npy(npy_path):
    return np.load(npy_path) 