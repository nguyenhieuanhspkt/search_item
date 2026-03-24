import sys
import pandas as pd
from pathlib import Path

# ============================================================
# 1. FIX ĐƯỜNG DẪN
# ============================================================
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
back_end_root = project_root.parent # search_item/back_end/

if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from core.normalize import Normalizer

# ============================================================
# 2. CHẠY TEST VÀ XUẤT HTML
# ============================================================
def main():
    INPUT_FILE = back_end_root / "Your_102_items.xlsx"
    CONFIG_DIR = project_root / "config"
    OUTPUT_HTML = project_root / "test_norm_results.html" # File kết quả
    
    if not INPUT_FILE.exists():
        print(f"❌ Không tìm thấy file: {INPUT_FILE}")
        return

    norm = Normalizer(config_path=str(CONFIG_DIR))
    
    print(f"📂 Đang đọc dữ liệu từ: {INPUT_FILE.name}")
    df = pd.read_excel(str(INPUT_FILE), engine="openpyxl")
    
    results = []

    print(f"🚀 Đang xử lý {len(df)} dòng vật tư...")
    for idx, row in df.iterrows():
        name = str(row.get("Tên", ""))
        spec = str(row.get("TS", ""))
        raw_text = f"{name} {spec}"
        
        normalized_text = norm.normalize(raw_text)
        
        results.append({
            "STT": row.get("STT", idx+1),
            "Nội dung gốc": raw_text,
            "Sau khi Normalize": normalized_text
        })

    # Chuyển list kết quả thành DataFrame
    df_result = pd.DataFrame(results)

    # Tạo CSS để bảng HTML trông đẹp và dễ nhìn
    style = """
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; }
        h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
        th, td { text-align: left; padding: 12px; border: 1px solid #ddd; word-wrap: break-word; max-width: 500px; }
        th { background-color: #007bff; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f1f1f1; }
        .stt { width: 50px; text-align: center; }
        .norm { color: #28a745; font-weight: bold; }
    </style>
    """

    # Xuất ra file HTML
    html_content = style + "<h2>Kết quả Test Module Normalize</h2>" + df_result.to_html(index=False, classes='table')
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"🎉 HOÀN TẤT! Hãy mở file sau bằng trình duyệt: \n👉 {OUTPUT_HTML.absolute()}")

if __name__ == "__main__":
    main()