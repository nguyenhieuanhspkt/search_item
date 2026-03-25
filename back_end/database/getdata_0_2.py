import pandas as pd
import os

def merge_vattu_and_cosogia(input_file, output_file):
    try:
        print(f"--- Đang đọc file: {input_file} ---")
        
        df_vattu = pd.read_excel(input_file, sheet_name="VatTu_Da_Clean")
        df_cosogia = pd.read_excel(input_file, sheet_name="CoSoGia_Da_Clean")

        key_vattu = 'Unnamed: 17'
        key_cosogia = 'Unnamed: 1'

        # 1. Chuẩn hóa Key
        df_vattu[key_vattu] = df_vattu[key_vattu].astype(str).str.strip()
        df_cosogia[key_cosogia] = df_cosogia[key_cosogia].astype(str).str.strip()

        # 2. QUAN TRỌNG: Loại bỏ trùng lặp ở bảng Cơ sở giá trước khi Merge
        # Việc này đảm bảo 1 mã giá chỉ tương ứng với 1 đơn giá duy nhất, 
        # tránh làm tăng dòng ở bảng VatTu.
        df_cosogia_unique = df_cosogia.drop_duplicates(subset=[key_cosogia], keep='first')
        
        num_duplicates = len(df_cosogia) - len(df_cosogia_unique)
        if num_duplicates > 0:
            print(f"⚠️ Phát hiện và loại bỏ {num_duplicates} dòng trùng mã giá trong Cơ sở giá để bảo vệ số lượng dòng.")

        # 3. Thực hiện Merge
        # Dùng how='left' để giữ nguyên toàn bộ dòng của df_vattu
        df_merged = pd.merge(
            df_vattu, 
            df_cosogia_unique, 
            left_on=key_vattu, 
            right_on=key_cosogia, 
            how='left'
        )

        # 4. Kiểm tra chéo số dòng
        if len(df_merged) == len(df_vattu):
            print(f"✅ Merge an toàn: Số dòng không thay đổi ({len(df_merged)} dòng).")
        else:
            print(f"❌ CẢNH BÁO: Số dòng bị thay đổi từ {len(df_vattu)} lên {len(df_merged)}!")

        # 5. Xuất kết quả
        df_merged.to_excel(output_file, index=False)
        print(f"🚀 Kết quả lưu tại: {os.path.abspath(output_file)}")

    except Exception as e:
        print(f"❌ Lỗi khi merge: {e}")

# --- THỰC THI ---
file_da_loc = "Ket_Qua_Loc_Cot.xlsx"
file_final = "Ket_Qua_Merge_Cuoi_Cung.xlsx"

if os.path.exists(file_da_loc):
    merge_vattu_and_cosogia(file_da_loc, file_final)