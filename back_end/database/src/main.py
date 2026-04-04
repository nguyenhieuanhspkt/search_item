import os
import pandas as pd
from dotenv import load_dotenv
import traceback

# Main chỉ import duy nhất từ processors.py
from processors import (
    step_1_to_3_load_data, 
    step_4_and_5_process_df1, 
    step_6_process_df2,
    process_phase_1_analytics,
    smart_vertical_grouping, 
    validate_financials,
    step_0_split_by_source, 
    fuzzy_match_history,
    compare_df5_with_others,
    match_erp_with_ai_logic # Hàm này giờ nằm trong processors.py
)

load_dotenv()
FILE_1 = os.getenv("FILE_1_PATH")
FILE_2 = os.getenv("FILE_2_PATH")
FILE_3 = os.getenv("FILE_3_PATH")
CHECKPOINT_FILE = "data_checkpoint_phase1.pkl"

def review_steps(use_checkpoint=True):
    # --- 1. NẠP DỮ LIỆU ---
    if use_checkpoint and os.path.exists(CHECKPOINT_FILE):
        print(f"⚡ [FAST LOAD] Nạp df1-df5 từ Checkpoint...")
        data_bundle = pd.read_pickle(CHECKPOINT_FILE)
        df1_final, df2_final = data_bundle['df1'], data_bundle['df2']
        df3_raw, df4_raw, df5_raw = data_bundle['df3'], data_bundle['df4'], data_bundle['df5']
    else:
        print(f"📂 [FULL LOAD] Nạp từ Excel...")
        df1_raw, df2_raw, df3_raw, df4_raw, df5_raw = step_1_to_3_load_data(FILE_1, FILE_2, FILE_3)
        df1_final = step_4_and_5_process_df1(df1_raw)
        df2_final = step_6_process_df2(df2_raw)
        if use_checkpoint:
            pd.to_pickle({'df1': df1_final, 'df2': df2_final, 'df3': df3_raw, 'df4': df4_raw, 'df5': df5_raw}, CHECKPOINT_FILE)

    # --- 2. LÀM SẠCH & GỘP DỌC (CHẶNG 1) ---
    df_anomalies_c1, df_unique = process_phase_1_analytics(df1_final, df2_final)
    df_step_1_5, df_anomalies_c2 = smart_vertical_grouping(df_unique)
    
    # Check tiền
    diff, _, t_final = validate_financials(df1_final, df_step_1_5)
    print(f"✅ XÁC THỰC: {'Khớp!' if diff < 100 else 'LỆCH!'} ({t_final:,.0f})")

    # --- 3. ĐỐI CHIẾU ĐA KHO (CHẶNG 2) ---
    df_baogia, df_others = step_0_split_by_source(df_step_1_5)

    # Đối chiếu S1 & File3 (Dùng Fuzzy)
    df_s1_final = fuzzy_match_history(df_baogia, df3_raw, "S1")
    df_df5_final = fuzzy_match_history(df_baogia, df5_raw, "File3")

    # Đối chiếu ERP (Dùng AI - Main gọi qua processors)
    df_erp_final = match_erp_with_ai_logic(df_baogia, df4_raw)

    # Đối chiếu ngược df5 làm gốc (Sheet 4)
    df_compare_df5 = compare_df5_with_others(df5_raw, df_step_1_5, df3_raw, df4_raw)

    # --- 4. XUẤT FILE ---
    with pd.ExcelWriter("2_Bao_Cao_Tham_Dinh_Phan_Loai.xlsx") as writer:
        df_s1_final.to_excel(writer, sheet_name="1. So sanh Kho S1", index=False)
        df_erp_final.to_excel(writer, sheet_name="2. So sanh Kho ERP (AI)", index=False)
        df_df5_final.to_excel(writer, sheet_name="3. So sanh File 3 (df5)", index=False)
        df_compare_df5.to_excel(writer, sheet_name="4. DOI_CHIEU_DF5_VOI_ALL", index=False)
        df_others.to_excel(writer, sheet_name="5. Nhom Hop Dong (Luu tru)", index=False)

    print(f"🎉 HOÀN THÀNH!")

if __name__ == "__main__":
    try:
        review_steps(use_checkpoint=True)
    except Exception as e:
        traceback.print_exc()