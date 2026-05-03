# 使用sklearn的余弦相似度计算
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 计算两条文本的余弦相似度
def analyze_duplicate_emb(emb1, emb2):
    """
    输入：两条文本的embedding向量
    输出：二者的余弦相似度分数（0~1之间，越高越相似）
    若计算异常，返回0.0
    """
    try:
        score = cosine_similarity([emb1], [emb2])[0][0]
        score = (score + 1) / 2 if score < 0 else score
        return float(score)
    except Exception:
        return 0.0
