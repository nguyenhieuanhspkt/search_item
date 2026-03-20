import sys
import os

# Thêm đường dẫn để nhận diện module core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Lấy đường dẫn của thư mục chứa file test_parser.py (chính là thư mục core)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Lấy đường dẫn thư mục cha (thư mục back_end)
parent_dir = os.path.dirname(current_dir)

# Thêm cả hai vào hệ thống để Python tìm thấy module 'core'
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    
    # Bây giờ import sẽ không còn lỗi nữa
try:
    from core.model_parser import ModelParser
    print("--- ✅ Import ModelParser thành công! ---")
except ImportError as e:
    # Nếu vẫn lỗi, thử import trực tiếp không qua 'core.'
    from model_parser import ModelParser
    print("--- ✅ Import trực tiếp thành công! ---")
def run_test():
    parser = ModelParser()
    
    # Danh sách các câu query mẫu thực tế tại nhà máy
    test_cases = [
        "Cảm biến áp suất Danfoss MBS 3000 0-10 bar G1/4",
        "Thép tấm SA240 Grade 316L dày 10mm khổ 1500x6000",
        "Màn hình HMI Siemens 6AV6647-0AA11-3AX0",
        "Vòng bi SKF 6205-2Z/C3 (phi 25x52x15)",
        "CB Mitsubishi NF125-SGV 3P 100A",
        "Ống inox SUS304 Phi 21.3 dày 2.1mm"
    ]

    print("="*50)
    print("🚀 HỆ THỐNG KIỂM TRA TRÍCH XUẤT MÃ VẬT TƯ (MODEL PARSER)")
    print("="*50)

    for i, query in enumerate(test_cases, 1):
        result = parser.parse(query)
        
        print(f"\n📝 Test {i}: '{query}'")
        print(f"   ├─ 🆔 Model/PN:  {result['models']}")
        print(f"   ├─ 🏷️ Nhãn hiệu: {result['brands']}")
        print(f"   ├─ 🏗️ Vật liệu:  {result['materials']}")
        print(f"   └─ 🔢 Thông số:  {result['numbers']}")
        print("-" * 30)

if __name__ == "__main__":
    run_test()