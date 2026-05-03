import os
import json
import time
from utils.embedding_utils import load_model, batch_vectorize, calc_file_hash, save_embeddings_npy, load_embeddings_npy
from .similarity import analyze_duplicate_emb  # 计算两条文本embedding的相似度
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from tqdm import tqdm

# 批量文本查重主函数
# 输入：
#   batch_path: 新批次文本的json文件路径（每条需有id和content字段）
#   history_path: 历史文本的json文件路径（同上）
#   output_path: 查重结果输出路径
# 输出：
#   结果写入output_path，包含本批次内部高相似pair和与历史最相似pair
# 用法见 test_dedup.py

def analyze_dedup(batch_path, history_path, output_path):
    start_time = time.time()
    # 读取新批次和历史数据
    with open(batch_path, "r", encoding="utf-8") as f:
        batch_notes = json.load(f)
    with open(history_path, "r", encoding="utf-8") as f:
        history_notes = json.load(f)
    # 提取文本内容
    batch_texts = [note["content"] for note in batch_notes]
    history_texts = [note["content"] for note in history_notes]
    print("[INFO] 正在加载embedding模型……")
    model = load_model()

    # 历史向量缓存机制
    history_embs_npy = history_path + ".embeddings.npy"
    history_hash_path = history_path + ".sha256.txt"
    history_hash = calc_file_hash(history_path)
    use_cache = False
    if os.path.exists(history_embs_npy) and os.path.exists(history_hash_path):
        with open(history_hash_path, "r", encoding="utf-8") as f:
            cached_hash = f.read().strip()
        if cached_hash == history_hash:
            try:
                history_embs = load_embeddings_npy(history_embs_npy)
                use_cache = True
                print(f"[INFO] 检测到历史笔记未变动，直接加载历史向量缓存（{history_embs_npy}）")
            except Exception as e:
                print(f"[WARN] 加载历史向量缓存失败，将重新向量化。原因：{e}")
    if not use_cache:
        print(f"[INFO] 历史笔记有变动或无缓存，正在向量化历史笔记……")
        t_hist = time.time()
        # 只向量化历史文本
        history_embs = model.encode(history_texts, show_progress_bar=True, batch_size=32)
        save_embeddings_npy(history_embs, history_embs_npy)
        with open(history_hash_path, "w", encoding="utf-8") as f:
            f.write(history_hash)
        print(f"[INFO] 历史笔记向量化完成并已缓存，用时 {time.time() - t_hist:.2f} 秒")

    print(f"[INFO] 正在进行批量向量化，共 {len(batch_texts)} 条新笔记，{len(history_texts)} 条历史笔记……")
    t0 = time.time()
    batch_embs = model.encode(batch_texts, show_progress_bar=True, batch_size=32)
    print(f"[INFO] 新批次向量化完成，用时 {time.time() - t0:.2f} 秒\n")

    # 本批次内部两两查重（批量矩阵优化版）
    print("[INFO] 正在查找本批次笔记中相似度超过90%的pair……")
    t1 = time.time()
    n = len(batch_notes)
    batch_high_sim_pairs = []
    if n > 1:
        # 批量计算 n*n 相似度矩阵
        sim_matrix = cosine_similarity(batch_embs, batch_embs)
        # 负值归一化（与原逻辑一致）
        sim_matrix = np.where(sim_matrix < 0, (sim_matrix + 1) / 2, sim_matrix)
        # 只取上三角（不含对角线）
        triu_indices = np.triu_indices(n, k=1)
        sim_scores = sim_matrix[triu_indices]
        idx_pairs = list(zip(triu_indices[0], triu_indices[1]))
        # 进度条模拟（分批输出进度）
        total = len(sim_scores)
        for idx, (score, (i, j)) in enumerate(zip(sim_scores, idx_pairs)):
            if score > 0.9:
                batch_high_sim_pairs.append({
                    "batch_id1": batch_notes[i]["id"],
                    "batch_id2": batch_notes[j]["id"],
                    "duplicate_score": float(score)
                })
            if (idx+1) % 100 == 0 or (idx+1) == total:
                print(f"[INFO] 已处理 {idx+1}/{total} 对……")
    print(f"[INFO] 本批次高相似度笔记对查重完成，用时 {time.time() - t1:.2f} 秒，共发现 {len(batch_high_sim_pairs)} 对\n")

    # 新批次与历史文本查重
    print("[INFO] 正在查找本批次每条笔记与历史笔记中最相似的那条……")
    batch_to_history = []
    t2 = time.time()
    for note, emb in zip(batch_notes, batch_embs):
        scores = cosine_similarity([emb], history_embs)[0]
        scores = np.where(scores < 0, (scores + 1) / 2, scores)  # 负值归一化
        max_idx = int(np.argmax(scores))
        max_score = float(scores[max_idx])
        max_id = history_notes[max_idx]["id"]
        batch_to_history.append({
            "batch_id": note["id"],
            "most_similar_history_id": max_id,
            "max_duplicate_score": max_score
        })
    print(f"[INFO] 本批次与历史最相似笔记查重完成，用时 {time.time() - t2:.2f} 秒\n")

    # 保存查重结果
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "batch_high_sim_pairs": batch_high_sim_pairs,
            "batch_to_history": batch_to_history
        }, f, ensure_ascii=False, indent=2)
    print(f"[INFO] analyze_dedup 完成，结果已保存到 {output_path}")
    print(f"\n[INFO] 全流程完成，总耗时：{time.time() - start_time:.2f} 秒\n") 

def analyze_potential(batch_path, history_path, hotwords_path, output_path, top_n=5):
    """
    内容潜力特征统计与加权评分
    输入：
        batch_path: 批次文本json路径（每条含id和content）
        history_path: 历史文本json路径（含爆文指数）
        hotwords_path: 热点关键词csv路径
        output_path: 评分结果输出路径
        top_n: Top-N爆文相似度加权，默认5
    输出：
        评分结果写入output_path，每条含结构分、相似度分、热点分、总分
    """
    import pandas as pd
    import re
    import numpy as np
    import json
    import time
    from sklearn.metrics.pairwise import cosine_similarity

    start_time = time.time()
    # 权重配置
    WEIGHTS = {'structure': 0.2, 'similarity': 0.5, 'hotword': 0.3}

    # 结构规范分
    def calc_structure_score(text):
        score = 1.0
        length = len(text)
        paragraphs = text.count('\n') + 1
        if length < 60:
            score -= 0.5
        elif length < 100:
            score -= 0.3
        elif length < 150:
            score -= 0.1
        if paragraphs < 2:
            score -= 0.2
        elif paragraphs > 5:
            score -= 0.05
        if re.search(r'[!！?？]{3,}', text):
            score -= 0.1
        if not (text.startswith('标题：') or re.search(r'酒店|民宿|体验|客栈|度假', text[:15])):
            score -= 0.1
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if len(lines) != len(set(lines)):
            score -= 0.1
        return max(round(score, 2), 0)

    # 读取数据
    with open(batch_path, encoding='utf-8') as f:
        batch_notes = json.load(f)
    with open(history_path, encoding='utf-8') as f:
        history_notes = json.load(f)
    hotwords_df = pd.read_csv(hotwords_path)
    hotword_tuples = list(hotwords_df.itertuples(index=False, name=None))
    def calc_hotword_score(text):
        hit = 0
        for _, _, kw in hotword_tuples:
            if kw in text:
                hit += 1
        return min(hit / max(len(hotword_tuples), 1), 1.0)

    from utils.embedding_utils import load_model, batch_vectorize, load_embeddings_npy
    model = load_model()
    batch_texts = [x['content'] for x in batch_notes]
    history_embs = load_embeddings_npy(history_path + '.embeddings.npy')
    history_scores = np.array([x.get('爆文指数', 0) for x in history_notes])
    explosive_mask = history_scores >= 80
    explosive_embs = history_embs[explosive_mask]
    # Top-N softmax加权相似度
    TOP_N = top_n
    batch_embs, _ = batch_vectorize(model, batch_texts, [])

    results = []
    for i, note in enumerate(batch_notes):
        text = note['content']
        struct_score = calc_structure_score(text)
        hotword_score = calc_hotword_score(text)
        if len(explosive_embs) > 0:
            sim = cosine_similarity(batch_embs[i].reshape(1, -1), explosive_embs).flatten()
            if len(sim) < TOP_N:
                top_idx = np.argsort(sim)[::-1]
            else:
                top_idx = np.argsort(sim)[-TOP_N:][::-1]
            top_sim = sim[top_idx]
            exp_sim = np.exp(top_sim)
            weights = exp_sim / np.sum(exp_sim)
            sim_score = float(np.sum(weights * top_sim))
        else:
            sim_score = 0.0
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
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'[INFO] analyze_potential 完成，结果已保存到 {output_path}')
    print(f'[INFO] 全流程完成，总耗时：{time.time() - start_time:.2f} 秒') 