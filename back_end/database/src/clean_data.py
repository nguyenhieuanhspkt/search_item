# FILE: main.py
import os
from dotenv import load_dotenv
from processors import step_1_to_3_load_data, step_4_and_5_process_df1, step_6_process_df2

# Lệnh này sẽ nạp các biến từ file .env vào hệ thống
load_dotenv()

# Lấy đường dẫn từ .env (Nếu không tìm thấy sẽ để trống)
FILE_1 = os.getenv("FILE_1_PATH")
FILE_2 = os.getenv("FILE_2_PATH")
FINAL_FILE = os.getenv("FINAL_FILE_NAME", "Ket_Qua_Mac_Dinh.xlsx")

def review_steps():
    # Kiểm tra xem đã lấy được file chưa
    if not FILE_1 or not FILE_2:
        print("❌ LỖI: Không tìm thấy đường dẫn file trong .env. Hiếu kiểm tra lại file .env nhé!")
        return

    print(f"📂 Đang xử lý File 1: {os.path.basename(FILE_1)}")
    
    # --- THỰC HIỆN CÁC STEP NHƯ ĐÃ THỎA THUẬN ---
    print("⏳ [Step 1-3] Đang nạp dữ liệu...")
    df1_raw, df2_raw, df3_raw = step_1_to_3_load_data(FILE_1, FILE_2)

    print("⏳ [Step 4-5] Đang xử lý df1 (Cột B-D, F, L, O, R)...")
    df1_final = step_4_and_5_process_df1(df1_raw)
    
    print("⏳ [Step 6] Đang xử lý df2 (Rename 8 cột đầu)...")
    df2_final = step_6_process_df2(df2_raw)

    # --- XUẤT KẾT QUẢ ĐỂ HIẾU REVIEW ---
    print("\n✅ KẾT QUẢ REVIEW DF1 (PL1.5 S3):")
    print(df1_final.head(10))
    
    print("\n✅ KẾT QUẢ REVIEW DF2 (Cơ sở giá):")
    # Hiển thị 5 dòng đầu và 10 cột đầu để kiểm tra tên cột mới
    print(df2_final.head(5).iloc[:, :10])

    # Lưu tạm ra Excel để Hiếu soi cho kỹ
    df1_final.to_excel("Review_Step5.xlsx", index=False)
    df2_final.to_excel("Review_Step6.xlsx", index=False)
    print(f"\n🚀 Đã xuất file Review_Step5.xlsx và Review_Step6.xlsx để Hiếu kiểm tra!")

if __name__ == "__main__":
    review_steps()