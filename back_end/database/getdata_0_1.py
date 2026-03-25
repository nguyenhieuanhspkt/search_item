import pandas as pd
import os

def export_marked_columns(input_file, output_file):
    try:
        # 1. Mở file Excel để lấy danh sách các sheet
        xl = pd.ExcelFile(input_file)
        writer = pd.ExcelWriter(output_file, engine='openpyxl')
        
        found_any = False

        for sheet_name in xl.sheet_names:
            # 2. Đọc dòng đầu tiên để tìm dấu 'x'
            # header=None để lấy toàn bộ từ dòng 1 (index 0)
            df_check = pd.read_excel(input_file, sheet_name=sheet_name, header=None, nrows=1)
            
            if df_check.empty:
                continue
                
            # Chuyển dòng 1 thành danh sách và tìm vị trí có chữ 'x'
            row_1 = df_check.iloc[0].astype(str).str.lower().str.strip()
            selected_indices = [i for i, val in enumerate(row_1) if val == 'x']
            
            if selected_indices:
                # 3. Đọc lại dữ liệu thực tế (bắt đầu từ dòng 2 làm tiêu đề - header=1)
                df_data = pd.read_excel(input_file, sheet_name=sheet_name, header=1)
                
                # Lọc lấy các cột theo vị trí index đã tìm thấy
                df_filtered = df_data.iloc[:, selected_indices]
                
                # 4. Ghi vào file excel mới
                df_filtered.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"✅ Đã lọc và lưu sheet: {sheet_name} ({len(selected_indices)} cột)")
                found_any = True
            else:
                print(f"⚠️ Sheet '{sheet_name}' không có đánh dấu 'x' ở dòng 1. Bỏ qua.")

        if found_any:
            writer.close()
            print(f"\n🚀 ĐÃ XUẤT FILE THÀNH CÔNG: {os.path.abspath(output_file)}")
        else:
            writer.close()
            print("❌ Không có dữ liệu nào được xuất vì không tìm thấy dấu 'x'.")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

# --- CHẠY ---
file_nguon = "Ket_Qua_Phu_Luc_109.xlsx"
file_dich = "Ket_Qua_Loc_Cot.xlsx"

if os.path.exists(file_nguon):
    export_marked_columns(file_nguon, file_dich)
else:
    print(f"❌ Không tìm thấy file nguồn: {file_nguon}")