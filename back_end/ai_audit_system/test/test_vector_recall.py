import sys
import pandas as pd
from pathlib import Path

# ============================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN (PROJECT ROOT)
# ============================================================
current_file = Path(__file__).resolve()
# Nhảy ngược 2 lần: test -> ai_audit_system
project_root = current_file.parent.parent 

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import Class từ pipeline.py (Đã fix lỗi import name)
try:
    from pipeline import MaterialAuditPipeline
except ImportError:
    print("❌ Lỗi: Không tìm thấy class MaterialAuditPipeline trong pipeline.py")
    sys.exit(1)

# ============================================================
# 2. CHẠY TEST RECALL TRÊN 102 ITEMS
# ============================================================
def main():
    # Đường dẫn các file
    INPUT_FILE = project_root / "data" / "raw" / "Your_102_items.xlsx"
    INDEX_PATH = project_root / "data" / "processed" / "faiss.index"
    META_PATH = project_root / "data" / "processed" / "faiss_meta.json"
    CONFIG_DIR = project_root / "config"
    OUTPUT_HTML = project_root / "test_recall_102_items.html"

    # Kiểm tra file hệ thống
    if not INDEX_PATH.exists():
        print(f"❌ Lỗi: Không tìm thấy Index tại {INDEX_PATH}. Chạy main.py trước!")
        return
    if not INPUT_FILE.exists():
        print(f"❌ Lỗi: Không tìm thấy file input tại {INPUT_FILE}")
        return

    # Khởi tạo Pipeline
    print("⚙️ Đang khởi tạo hệ thống và nạp Index...")
    pipe = MaterialAuditPipeline(config_path=str(CONFIG_DIR))
    pipe.load_index(str(INDEX_PATH), str(META_PATH))

    # Đọc dữ liệu 102 món
    print(f"📂 Đang đọc dữ liệu từ: {INPUT_FILE.name}")
    df_input = pd.read_excel(INPUT_FILE, engine="openpyxl")
    
    # Bạn có thể chọn chạy hết hoặc chạy 30 dòng đầu để test nhanh
    # test_df = df_input.head(30) 
    test_df = df_input 

    results_list = []
    print(f"🚀 Đang đối soát {len(test_df)} món vật tư...")

    for idx, row in test_df.iterrows():
        # Lấy Tên và Thông số từ file Input
        name_in = str(row.get("Tên", "")).strip()
        spec_in = str(row.get("TS", "")).strip()
        raw_query = f"{name_in} {spec_in}"

        # 1. Normalize query để soi trong HTML
        q_norm = pipe.normalizer.normalize(raw_query)

        # 2. Gọi hàm search mới định nghĩa trong pipeline.py
        search_res = pipe.search(raw_query, top_k=1)
        
        res_data = {
            "STT": row.get("STT", idx + 1),
            "Input Gốc": raw_query,
            "Normalize": q_norm,
            "Mã ERP Khớp": "-",
            "Kết quả ERP Master": "❌ KHÔNG TÌM THẤY",
            "Score": 0.0
        }

        if search_res:
            top_1 = search_res[0]
            meta = top_1['metadata']
            
            # Lấy tên cột linh hoạt (NXT hoặc N)
            erp_name = meta.get("Tên vật tư (NXT)", meta.get("Tên vật tư (N", ""))
            erp_spec = meta.get("Thông số kỹ thuật", "")
            
            res_data["Mã ERP Khớp"] = meta.get("Mã vật tư", "N/A")
            res_data["Kết quả ERP Master"] = f"{erp_name} {erp_spec}"
            res_data["Score"] = round(top_1['score'], 4)

        results_list.append(res_data)

    # Xuất báo cáo HTML
    df_final = pd.DataFrame(results_list)
    
    style = """
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 30px; background: #f4f7f6; }
        h2 { color: #2c3e50; text-align: center; }
        table { border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        th, td { padding: 12px 15px; border: 1px solid #ddd; text-align: left; }
        th { background: #3498db; color: white; font-size: 14px; }
        tr:hover { background: #f1f1f1; }
        .high { color: #27ae60; font-weight: bold; }
        .low { color: #e74c3c; font-weight: bold; }
        .norm { color: #7f8c8d; font-size: 0.85em; font-style: italic; }
    </style>
    """

    def format_score(val):
        color_class = 'high' if val > 0.8 else ('low' if val < 0.6 else '')
        return f'<span class="{color_class}">{val}</span>'

    df_final['Score'] = df_final['Score'].apply(format_score)
    df_final['Normalize'] = df_final['Normalize'].apply(lambda x: f'<span class="norm">{x}</span>')

    html_out = f"<html><head>{style}</head><body><h2>Kết quả Thử nghiệm Đối soát (Recall Test)</h2>"
    html_out += df_final.to_html(index=False, escape=False) + "</body></html>"

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"🎉 HOÀN TẤT! Đã xuất báo cáo tại: {OUTPUT_HTML.absolute()}")

if __name__ == "__main__":
    main()