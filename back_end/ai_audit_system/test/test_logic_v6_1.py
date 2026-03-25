import pandas as pd
from pathlib import Path

from ai_audit_system.pipeline import MaterialAuditPipeline


# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN (relative từ ROOT)
# ==========================================
ROOT_DIR = Path.cwd()  # 👈 chạy từ ROOT nên cwd chính là root
child_root_dir = ROOT_DIR / "search_item2" / "search_item"
back_end_dir = child_root_dir / "back_end"
data_child_root_dir = child_root_dir/"back_end" /"ai_audit_system"
INPUT_EXCEL = data_child_root_dir/"raw"/"Your_102_items.xlsx"
OUTPUT_EXCEL = back_end_dir / "Ket_Qua_Thanh_Pham_V6_2.xlsx"

CONFIG_DIR = back_end_dir / "ai_audit_system" / "config"
LOG_FILE = back_end_dir / "ai_audit_system" / "logs" / "audit_test.json"


def run_test():
    # Debug để chắc chắn đang đứng đúng ROOT
    print(f"📍 Current working dir: {ROOT_DIR}")

    # Kiểm tra file input
    if not INPUT_EXCEL.exists():
        print(f"❌ Không tìm thấy file: {INPUT_EXCEL}")
        return

    # Khởi tạo pipeline
    pipeline = MaterialAuditPipeline(config_path=str(CONFIG_DIR))

    # Đọc dữ liệu
    print(f"📂 Đang đọc: {INPUT_EXCEL.name}")
    df_input = pd.read_excel(INPUT_EXCEL)

    # Chạy pipeline
    print("🧠 AI đang xử lý...")
    df_result = pipeline.process(df_input)

    # Xuất kết quả
    df_result.to_excel(OUTPUT_EXCEL, index=False)

    print("\n" + "=" * 50)
    print("🚀 HOÀN THÀNH")
    print(f"📊 Output: {OUTPUT_EXCEL}")
    print(f"📝 Log: {LOG_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    run_test()