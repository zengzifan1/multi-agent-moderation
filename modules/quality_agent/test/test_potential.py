# 内容潜力分析功能测试脚本
import sys
from pathlib import Path

# 获取项目根目录并添加到系统路径
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.append(project_root)


from agents.text_quality import analyze_potential

if __name__ == '__main__':
    data_dir = Path(project_root) / "data"
    output_dir = Path(project_root) / "outputs"
    batch_path = str(data_dir / "batch_notes.json")
    history_path = str(data_dir / "history_notes.json")
    hotwords_path = str(data_dir / "热点关键词.csv")
    output_path = str(output_dir / "feature_scores.json")
    analyze_potential(batch_path, history_path, hotwords_path, output_path)