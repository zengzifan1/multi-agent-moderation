# 内容潜力特征统计与加权评分脚本
# 读取批次笔记、历史笔记、embedding和热点关键词，对每条批次文本统计结构规范分、爆文相似度分、热点覆盖分，按权重加权输出内容潜力分。
#
# 新版爆文相似度分说明：
#   - 先筛选历史笔记中“爆文”（如爆文指数>=80）的embedding，作为参考库。
#   - 对每条批次文本，计算其embedding与所有历史爆文embedding的余弦相似度，取Top-N（如5）最大值。
#   - 对Top-N相似度做softmax归一化，直接加权求和（不乘爆文指数），作为similarity_score，分数范围0~1。
#   - 这样分布更分散，区分度更高。
#
# 最终加权公式：
#   total_score = structure_score * 0.2 + similarity_score * 0.5 + hotword_score * 0.3
#   其中：
#     - structure_score：结构规范分（规则法）
#     - similarity_score：爆文相似度分（Top-N softmax加权相似度）
#     - hotword_score：热点关键词覆盖分（命中率）

import sys, os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import numpy as np
import pandas as pd
import re
from utils.embedding_utils import load_model, batch_vectorize, load_embeddings_npy
from sklearn.metrics.pairwise import cosine_similarity

# 路径配置
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '../outputs')
BATCH_FILE = os.path.join(DATA_DIR, 'batch_notes.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history_notes.json')
HISTORY_EMB_FILE = os.path.join(DATA_DIR, 'history_notes.json.embeddings.npy')
HOTWORDS_FILE = os.path.join(DATA_DIR, '热点关键词.csv')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'feature_scores.json')

# 权重配置
WEIGHTS = {
    'structure': 0.2,
    'similarity': 0.5,
    'hotword': 0.3
}

TOP_N = 5  # Top-N爆文相似度加权

# 结构规范分（更细致规则：字数、段落数、标点规范、标题、重复句等）
def calc_structure_score(text):
    score = 1.0
    length = len(text)
    paragraphs = text.count('\n') + 1
    # 字数
    if length < 60:
        score -= 0.5
    elif length < 100:
        score -= 0.3
    elif length < 150:
        score -= 0.1
    # 段落
    if paragraphs < 2:
        score -= 0.2
    elif paragraphs > 5:
        score -= 0.05
    # 标点规范（连续标点、异常符号）
    if re.search(r'[!！?？]{3,}', text):
        score -= 0.1
    # 标题（如有“标题：”或首行10字内有“酒店/民宿/体验”等关键词）
    if not (text.startswith('标题：') or re.search(r'酒店|民宿|体验|客栈|度假', text[:15])):
        score -= 0.1
    # 重复句（简单判定：有重复行）
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) != len(set(lines)):
        score -= 0.1
    return max(round(score, 2), 0)

# 读取热点关键词表，返回list of dict
hotwords_df = pd.read_csv(HOTWORDS_FILE)
hotword_tuples = list(hotwords_df.itertuples(index=False, name=None))

# 统计文本命中热点关键词数量
def calc_hotword_score(text):
    hit = 0
    for _, _, kw in hotword_tuples:
        if kw in text:
            hit += 1
    # 简单归一化（命中数/总数）
    return min(hit / max(len(hotword_tuples), 1), 1.0)

if __name__ == '__main__':
    start_time = time.time()
    # 读取数据
    with open(BATCH_FILE, encoding='utf-8') as f:
        batch_notes = json.load(f)
    with open(HISTORY_FILE, encoding='utf-8') as f:
        history_notes = json.load(f)
    history_embs = load_embeddings_npy(HISTORY_EMB_FILE)
    history_scores = np.array([x.get('爆文指数', 0) for x in history_notes])

    # 只用爆文（如爆文指数>=80）做相似度参考
    explosive_mask = history_scores >= 80
    explosive_embs = history_embs[explosive_mask]

    # 加载embedding模型
    model = load_model()
    batch_texts = [x['content'] for x in batch_notes]
    batch_embs, _ = batch_vectorize(model, batch_texts, [])

    results = []
    for i, note in enumerate(batch_notes):
        text = note['content']
        # 结构分
        struct_score = calc_structure_score(text)
        # 热点分
        hotword_score = calc_hotword_score(text)
        # 爆文相似度分（Top-N softmax加权相似度）
        if len(explosive_embs) > 0:
            sim = cosine_similarity(batch_embs[i].reshape(1, -1), explosive_embs).flatten()
            if len(sim) < TOP_N:
                top_idx = np.argsort(sim)[::-1]
            else:
                top_idx = np.argsort(sim)[-TOP_N:][::-1]
            top_sim = sim[top_idx]
            # softmax归一化权重
            exp_sim = np.exp(top_sim)
            weights = exp_sim / np.sum(exp_sim)
            sim_score = float(np.sum(weights * top_sim))  # 直接加权相似度
        else:
            sim_score = 0.0
        # 加权总分
        total = (struct_score * WEIGHTS['structure'] +
                 sim_score * WEIGHTS['similarity'] +
                 hotword_score * WEIGHTS['hotword'])
        results.append({
            'id': note['id'],
            'structure_score': round(struct_score, 3),
            'similarity_score': round(sim_score, 3),
            'hotword_score': round(hotword_score, 3),
            'total_score': round(total, 3)
        })

    # 输出结果
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print(f'特征统计与加权评分已输出到: {OUTPUT_FILE}')
    print(f'运行总耗时：{elapsed:.2f} 秒') 