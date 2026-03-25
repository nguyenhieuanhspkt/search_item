import pandas as pd
import re
from collections import Counter
import os
import yaml

def enrich_and_update_domains(file_path, yaml_path):
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file Excel tại: {file_path}")
        return

    print(f"🚀 Bước 1: Đang khai thác dữ liệu từ {file_path}...")
    df = pd.read_excel(file_path)
    # Lấy dữ liệu văn bản từ cột tên vật tư (thường là cột 1 hoặc 2)
    text_data = " ".join(df.iloc[:, 1].astype(str).tolist()).lower()
    words = re.findall(r'\b[a-z]{3,}\b', text_data)
    
    # Lấy top 300 từ phổ biến để có nhiều lựa chọn hơn
    common_words = [word for word, count in Counter(words).most_common(300) if count > 10]

    print(f"🚀 Bước 2: Đang đọc cấu trúc {yaml_path}...")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Định nghĩa các bộ lọc để AI tự phân loại vào nhóm
    # Hiếu có thể thêm các từ đặc trưng vào đây để script tự học tốt hơn
    filters = {
        'valve': ['valve', 'van', 'gate', 'globe', 'ball', 'check', 'actuator', 'solenoid', 'diaphragm', 'bonnet'],
        'sootblower': ['sootblower', 'poppet', 'lance', 'tube', 'cleaner', 'blower'],
        'mechanical': ['bearing', 'vong', 'bi', 'gasket', 'seal', 'oring', 'packing', 'bushing', 'coupling', 'joint', 'bolt', 'nut', 'screw', 'washer'],
        'electrical': ['switch', 'relay', 'sensor', 'cable', 'module', 'connector', 'motor', 'coil', 'voltage', 'circuit'],
        'steel': ['plate', 'steel', 'inox', 'hardox', 'iron', 'metal', 'sus'],
        'brands': ['chesterton', 'philips', 'komatsu', 'martin', 'leco', 'skf', 'fag', 'nachi', 'micos', 'yujin']
    }

    print(f"🚀 Bước 3: Đang tự động phân loại {len(common_words)} từ khóa...")
    
    # Tạo nhóm brands nếu chưa có trong yaml
    if 'brands' not in config['domain_rules']:
        config['domain_rules']['brands'] = {'keywords': []}

    added_count = 0
    for word in common_words:
        # Bỏ qua các từ nối/từ vô nghĩa (Stopwords)
        if word in ['cho', 'trong', 'theo', 'cua', 'and', 'with', 'the', 'for', 'tinh', 'quy', 'tăng', 'ghi']:
            continue
            
        for category, triggers in filters.items():
            # Nếu từ khóa khớp với bộ lọc của nhóm nào thì đẩy vào nhóm đó
            if any(trigger in word for trigger in triggers):
                current_keywords = config['domain_rules'][category]['keywords']
                if word not in current_keywords:
                    current_keywords.append(word)
                    added_count += 1
                break # Ưu tiên nhóm đầu tiên khớp

    # Ghi lại vào file YAML
    print(f"🚀 Bước 4: Đang ghi đè tri thức mới vào {yaml_path}...")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print(f"✅ THÀNH CÔNG: Đã làm giàu thêm {added_count} từ khóa chuyên ngành!")

if __name__ == "__main__":
    # Tự động tính toán đường dẫn
    current_file = os.path.abspath(__file__)
    utils_dir = os.path.dirname(current_file)
    backend_root = os.path.dirname(os.path.dirname(utils_dir))
    
    # Đường dẫn file Excel và file YAML
    # Hiếu kiểm tra lại xem folder 'config' nằm ở đâu nhé. 
    # Nếu config nằm cùng cấp với ai_audit_system thì dùng backend_root
    excel_path = os.path.join(backend_root, "ai_audit_system", "data", "raw", "Data_For_Meili.xlsx")
    yaml_path = os.path.join(backend_root, "ai_audit_system", "config", "domains.yaml")

    print(f"📍 Excel: {excel_path}")
    print(f"📍 YAML: {yaml_path}")
    
    enrich_and_update_domains(excel_path, yaml_path)