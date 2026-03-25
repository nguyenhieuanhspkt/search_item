import pandas as pd
import os

def get_clean_df(file_path, sheet_name_keyword, header_keyword="Mã hạng mục"):
    """Hàm đọc, làm sạch và ĐIỀN ĐẦY mã hạng mục."""
    try:
        xl = pd.ExcelFile(file_path)
        actual_sheet_name = next((s for s in xl.sheet_names if sheet_name_keyword in s), None)
        
        if not actual_sheet_name:
            print(f"❌ Không tìm thấy sheet: '{sheet_name_keyword}'")
            return None

        # Đọc thô để tìm dòng tiêu đề
        df_temp = pd.read_excel(file_path, sheet_name=actual_sheet_name, header=None)
        
        header_row_index = 0
        for i, row in df_temp.iterrows():
            # Kiểm tra dòng chứa "Mã hạng mục" hoặc "lã hạng mục" (do lỗi font hoặc gõ)
            row_str = row.astype(str).values
            if any(header_keyword in s for s in row_str) or any("hạng mục" in s.lower() for s in row_str):
                header_row_index = i
                break
        
        # Đọc dữ liệu chuẩn
        df = pd.read_excel(file_path, sheet_name=actual_sheet_name, header=header_row_index)
        
        # Làm sạch cột và hàng trống hoàn toàn
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]

        # --- BƯỚC XỬ LÝ BỔ SUNG: ĐIỀN ĐẦY MÃ HẠNG MỤC ---
        # Giả sử cột đầu tiên là cột mã hạng mục (như hình bạn gửi)
        col_ma_hm = df.columns[0] 
        
        # 1. Chuyển các ô chỉ có khoảng trắng thành NaN để ffill nhận diện được
        df[col_ma_hm] = df[col_ma_hm].replace(r'^\s*$', pd.NA, regex=True)
        
        # 2. Thực hiện Forward Fill (Điền từ trên xuống)
        df[col_ma_hm] = df[col_ma_hm].ffill()
        
        print(f"✅ Đã Clean và Fill mã hạng mục: '{actual_sheet_name}'")
        return df
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return None

def export_to_excel(dict_dfs, output_name="Ket_Qua_Thanh_Pham.xlsx"):
    try:
        current_dir = os.getcwd()
        full_path = os.path.join(current_dir, output_name)
        
        # Chèn thêm một dòng trống ở trên cùng để người dùng đánh dấu "x" như bước trước bạn muốn
        with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
            for sheet_name, df in dict_dfs.items():
                if df is not None:
                    # Tạo dataframe phụ chứa dòng trống để sau này bạn đánh dấu x
                    df_final = pd.DataFrame([[""] * len(df.columns)], columns=df.columns)
                    df_final = pd.concat([df_final, df], ignore_index=True)
                    
                    df_final.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"🚀 Xuất file thành công tại: {full_path}")
    except Exception as e:
        print(f"❌ Lỗi khi xuất file: {e}")

# --- QUY TRÌNH CHẠY ---
file_input = r'D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\Năm 2026\Thẩm định 109_hieuna_3\PL1_Dự toán Trung tu tổ máy S3 năm 2026_Phần tổ máy.xlsx'

# 1. Lấy dữ liệu (Hàm get_clean_df bây giờ đã có tự động Fill Down mã hạng mục)
df_vattu = get_clean_df(file_input, "PL1.5 DT VẬT TƯ TM")
df_cosogia = get_clean_df(file_input, "Cơ sở giá")

# 2. Gom vào dictionary
data_to_export = {
    "VatTu_Da_Clean": df_vattu,
    "CoSoGia_Da_Clean": df_cosogia
}

# 3. Xuất file (File này sẽ có dòng 1 trống để bạn đánh dấu x)
export_to_excel(data_to_export, "Ket_Qua_Phu_Luc_109.xlsx")