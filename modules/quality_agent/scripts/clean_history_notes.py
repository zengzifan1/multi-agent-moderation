# 清理历史笔记，去除标题前缀，并保证顺序：id, content, 爆文指数

import json
import re
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
history_path = os.path.join(project_root, "data", "history_notes.json")
output_path = os.path.join(project_root, "data", "history_notes_clean.json")

# 读取原始数据
with open(history_path, 'r', encoding='utf-8') as f:
    notes = json.load(f)

cleaned_notes = []
for note in notes:
    content = note.get('content', '')
    # 去除“标题：xxx \n ”前缀
    clean_content = re.sub(r'^标题：.*?\n\s*', '', content)
    new_note = {}
    # 保证顺序：id, content, 爆文指数
    if 'id' in note:
        new_note['id'] = note['id']
    new_note['content'] = clean_content
    if '爆文指数' in note:
        new_note['爆文指数'] = note['爆文指数']
    cleaned_notes.append(new_note)

# 写入新文件，字段换行显示
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('[\n')
    for idx, note in enumerate(cleaned_notes):
        f.write('  {\n')
        fields = []
        if 'id' in note:
            fields.append(f'    "id": {json.dumps(note["id"], ensure_ascii=False)}')
        fields.append(f'    "content": {json.dumps(note["content"], ensure_ascii=False)}')
        if '爆文指数' in note:
            fields.append(f'    "爆文指数": {json.dumps(note["爆文指数"], ensure_ascii=False)}')
        f.write(',\n'.join(fields))
        f.write('\n  }')
        if idx < len(cleaned_notes) - 1:
            f.write(',\n')
        else:
            f.write('\n')
    f.write(']\n')

print(f"处理完成，结果已保存到 {output_path}")