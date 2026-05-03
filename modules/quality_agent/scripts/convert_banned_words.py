# 将抖音违禁词总表转换为CSV格式并保存到指定位置
# 保持原有表头格式：violation_level,category,keyword
# violation_level使用高中低风险等级
# category使用具体分类名称
# 使用UTF-8-BOM编码避免Excel打开乱码

import json
import csv
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_dir = os.path.join(project_root, "data")

# 输入文件路径（请放到 data 目录下）
INPUT_FILE = os.path.join(data_dir, "banned_words.json")

# 输出文件路径
OUTPUT_FILE = os.path.join(data_dir, "banned_words.csv")

# 风险等级映射
RISK_LEVEL_MAPPING = {
    "严重违规": "高",
    "违反广告法": "中",
    "违反平台投放规则": "中",
    "涉嫌引诱留资": "中",
    "潜在风险": "中",
    "其他风险": "中"
}

def convert_json_to_csv():
    # 读取JSON文件
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 准备CSV数据
    rows = []
    
    # 遍历每个分类
    for category, keywords in data.items():
        # 获取风险等级
        violation_level = RISK_LEVEL_MAPPING.get(category, "中")  # 默认为中风险
        
        # 为每个关键词添加信息
        for keyword in keywords:
            # 处理特殊情况，如数字1需要转换为字符串
            if isinstance(keyword, int):
                keyword = str(keyword)
                
            rows.append({
                'violation_level': violation_level,
                'category': category,
                'keyword': keyword
            })
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # 写入CSV文件，使用UTF-8-BOM编码避免Excel打开乱码
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['violation_level', 'category', 'keyword'])
        
        # 写入表头
        writer.writeheader()
        
        # 写入数据
        writer.writerows(rows)
    
    print(f"转换完成，共处理 {len(rows)} 条违禁词")
    print(f"输出文件: {OUTPUT_FILE}")

if __name__ == "__main__":
    convert_json_to_csv()