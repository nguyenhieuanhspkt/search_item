import os
import pandas as pd
from dotenv import load_dotenv
import traceback

# Import các hàm xử lý từ processors.py
from processors import (
    step_1_to_3_load_data, 
    step_4_and_5_process_df1, 
    step_6_process_df2,
    process_phase_1_analytics,
    smart_vertical_grouping, 
    validate_financials,
    step_0_split_by_source, 
    fuzzy_match_history
)

# 1. NẠP CẤU HÌNH TỪ FILE .ENV
load_dotenv()

FILE_1 = os.getenv("FILE_1_PATH")
FILE_2 = os.getenv("FILE_2_PATH")
# File kết quả cuối cùng của Chặng 2
FINAL_AUDIT_FILE = "2_Bao_Cao_Tham_Dinh_Da_Kho.xlsx"

# Đường dẫn file tạm để Debug siêu nhanh
CHECKPOINT_FILE = "data_checkpoint_phase1.pkl"

def review_steps(use_checkpoint=True):
    """
    Hàm điều khiển chính: Nạp -> Chặng 1 (Làm sạch) -> Tiền xử lý (Gộp dọc) -> Chặng 2 (So khớp ngang)
    """
    # --- KIỂM TRA ĐẦU VÀO ---
    if not FILE_1 or not FILE_2:
        print("❌ LỖI: Hiếu ơi, kiểm tra lại file .env nhé.")
        return

    # --- BƯỚC 1 ĐẾN 6: NẠP VÀ CHUẨN HÓA DỮ LIỆU THÔ ---
    if use_checkpoint and os.path.exists(CHECKPOINT_FILE):
        print(f"⚡ [FAST LOAD] Đang nạp toàn bộ dữ liệu (df1-df4) từ Checkpoint...")
        data_bundle = pd.read_pickle(CHECKPOINT_FILE)
        df1_final = data_bundle['df1']
        df2_final = data_bundle['df2']
        df3_raw = data_bundle['df3']
        df4_raw = data_bundle['df4']
    else:
        print(f"📂 [FULL LOAD] Đang đọc dữ liệu từ các file Excel gốc...")
        
        # Step 1-3 & Nạp thêm df4 (ERP)
        # Lưu ý: Cập nhật lại hàm này trong processors.py để return thêm df4
        df1_raw, df2_raw, df3_raw, df4_raw = step_1_to_3_load_data(FILE_1, FILE_2)
        
        print("🛠  Đang xử lý df1 (Dự toán) và Populate Down Mã HM...")
        df1_final = step_4_and_5_process_df1(df1_raw)
        
        print("🛠  Đang chuẩn hóa df2 (Cơ sở giá)...")
        df2_final = step_6_process_df2(df2_raw)
        
        # Lưu Checkpoint bao gồm cả các kho giá lịch sử để lần sau không cần chờ load Excel
        if use_checkpoint:
            pd.to_pickle({
                'df1': df1_final, 
                'df2': df2_final, 
                'df3': df3_raw, 
                'df4': df4_raw
            }, CHECKPOINT_FILE)
            print(f"💾 Đã lưu Checkpoint mới (df1-df4) tại: {CHECKPOINT_FILE}")

    # --- CHẶNG 1: PHÂN TÍCH BẤT THƯỜNG & TỔNG HỢP DUY NHẤT ---
    print(f"\n{'='*60}\n🚀 ĐANG THỰC HIỆN CHẶNG 1: KIỂM SOÁT & LÀM SẠCH\n{'='*60}")
    
    # Gọi hàm phân tích (Bóc phốt giá ban đầu + Aggregation theo MG)
    df_anomalies_c1, df_unique = process_phase_1_analytics(df1_final, df2_final)

    # --- TIỀN XỬ LÝ CHẶNG 2: GỘP THÔNG MINH & SOI GIÁ LẦN 2 ---
    print(f"\n🧠 Đang thực hiện Gộp thông minh hàng dọc (Vertical Matching)...")
    df_step_1_5, df_anomalies_c2 = smart_vertical_grouping(df_unique)

    # Hợp nhất tất cả báo cáo bất thường giá (C1 + C2)
    df_total_anomalies = pd.concat([df_anomalies_c1, df_anomalies_c2]).drop_duplicates()

    if not df_total_anomalies.empty:
        anomaly_file = "1_Bao_Cao_Bat_Thuong_Gia.xlsx"
        df_total_anomalies.to_excel(anomaly_file, index=False)
        print(f"⚠️  CẢNH BÁO: Phát hiện {len(df_total_anomalies)} dòng vật tư sai lệch đơn giá!")
        print(f"👉 Chi tiết tại: {os.path.abspath(anomaly_file)}")

    # Xác thực tài chính
    diff, t_raw, t_final = validate_financials(df1_final, df_step_1_5)
    if diff < 100:
        print(f"✅ XÁC THỰC: Khớp tiền tuyệt đối! (Tổng: {t_final:,.0f})")
    else:
        print(f"❌ LỖI: Lệch tiền {diff:,.0f} sau khi gộp!")

    # --- CHẶNG 2: SO KHỚP CHI TIẾT (HÀNG NGANG) ---
    from processors import step_0_split_by_source, fuzzy_match_history

    # STEP 0: Tách nhóm Báo giá
    df_baogia, df_others = step_0_split_by_source(df_step_1_5)

    # STEP 1: So khớp với Kho S1 (Bảng 1)
    df_s1_final = fuzzy_match_history(df_baogia, df3_raw, "S1")
    df_s1_final = df_s1_final.sort_values(by='Diff_Pct_S1', ascending=False)

    # STEP 2: So khớp với Kho ERP 20k (Bảng 2)
    # So trực tiếp từ df_baogia để độc lập với S1
    df_erp_final = fuzzy_match_history(df_baogia, df4_raw, "ERP_20k")
    df_erp_final = df_erp_final.sort_values(by='Diff_Pct_ERP_20k', ascending=False)

    # --- XUẤT FILE EXCEL NHIỀU SHEET ---
    with pd.ExcelWriter("2_Bao_Cao_Tham_Dinh_Phan_Loai.xlsx") as writer:
        df_s1_final.to_excel(writer, sheet_name="1. So sanh Kho S1", index=False)
        df_erp_final.to_excel(writer, sheet_name="2. So sanh Kho ERP", index=False)
        df_others.to_excel(writer, sheet_name="3. Nhom Hop Dong (Luu tru)", index=False)

    print(f"\n🎉 Đã hoàn thành! Hiếu mở file '2_Bao_Cao_Tham_Dinh_Phan_Loai.xlsx' để xem các mức cảnh báo nhé.")

if __name__ == "__main__":
    try:
        # Nhớ xóa file .pkl nếu Hiếu sửa file Excel gốc hoặc đổi logic nạp
        review_steps(use_checkpoint=True)
    except Exception as e:
        print(f"\n❌ LỖI HỆ THỐNG: {e}")
        traceback.print_exc()