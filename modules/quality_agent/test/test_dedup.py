# 文本查重功能测试脚本
import sys
from pathlib import Path

# 获取项目根目录并添加到系统路径
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.append(project_root)

from agents.text_quality import analyze_dedup

# 使用相对路径，便于复现与开源
data_dir = Path(project_root) / "data"
output_dir = Path(project_root) / "outputs"
batch_path = str(data_dir / "batch_notes.json")
history_path = str(data_dir / "history_notes.json")
output_path = str(output_dir / "deduplication_local_results.json")

# 执行查重，结果会输出到 output_path
analyze_dedup(batch_path, history_path, output_path)