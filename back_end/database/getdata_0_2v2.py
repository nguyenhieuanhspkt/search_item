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

        # 2. XỬ LÝ THÔNG MINH: Giữ lại dòng nhiều thông tin nhất
        # Tạo một cột tạm tính tổng số ô không trống (non-null) trên mỗi dòng
        df_cosogia['info_count'] = df_cosogia.notna().sum(axis=1)

        # Sắp xếp theo Mã giá và số lượng thông tin (giảm dần)
        # Dòng nào nhiều thông tin hơn sẽ nhảy lên trên
        df_cosogia = df_cosogia.sort_values(by=[key_cosogia, 'info_count'], ascending=[True, False])

        # Thực hiện loại bỏ trùng lặp, giữ lại dòng đầu tiên (đã là dòng nhiều thông tin nhất)
        df_cosogia_unique = df_cosogia.drop_duplicates(subset=[key_cosogia], keep='first')
        
        # Xóa cột tạm info_count để bảng sạch sẽ
        df_cosogia_unique = df_cosogia_unique.drop(columns=['info_count'])

        num_duplicates = len(df_cosogia) - len(df_cosogia_unique)
        if num_duplicates > 0:
            print(f"⚠️ Đã lọc trùng: Giữ lại {len(df_cosogia_unique)} dòng đầy đủ thông tin nhất, loại bỏ {num_duplicates} dòng thiếu thông tin.")

        # 3. Thực hiện Merge
        df_merged = pd.merge(
            df_vattu, 
            df_cosogia_unique, 
            left_on=key_vattu, 
            right_on=key_cosogia, 
            how='left'
        )

        # 4. Kiểm tra an toàn
        if len(df_merged) == len(df_vattu):
            print(f"✅ Merge an toàn: Số dòng không đổi ({len(df_merged)} dòng).")
        else:
            print(f"❌ CẢNH BÁO: Số dòng thay đổi (Vật tư: {len(df_vattu)} -> Merge: {len(df_merged)})")

        # 5. Xuất kết quả
        df_merged.to_excel(output_file, index=False)
        print(f"🚀 Kết quả đã được tối ưu lưu tại: {os.path.abspath(output_file)}")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

# --- THỰC THI ---
file_da_loc = "Ket_Qua_Loc_Cot.xlsx"
file_final = "Ket_Qua_Merge_Cuoi_Cung.xlsx"

if os.path.exists(file_da_loc):
    merge_vattu_and_cosogia(file_da_loc, file_final)