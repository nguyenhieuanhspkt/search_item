import pandas as pd
import os

def final_data_cleaning(input_file, output_file):
    try:
        # 1. Đọc file kết quả merge
        print(f"--- Đang tiến hành làm sạch dữ liệu chuyên sâu ---")
        df = pd.read_excel(input_file)

        # Kiểm tra sự tồn tại của các cột
        required_cols = ["Unnamed: 11_x", "Unnamed: 15_x"]
        for col in required_cols:
            if col not in df.columns:
                print(f"❌ Cảnh báo: Không tìm thấy cột '{col}'")
                print(f"Danh sách cột hiện có: {df.columns.tolist()}")
                return

        # 2. Xử lý cột Unnamed: 15_x (Loại bỏ các dòng có giá trị trống)
        # dropna sẽ xóa các dòng có NaN (ô trống)
        df_cleaned = df.dropna(subset=["Unnamed: 15_x"])

        # 3. Xử lý cột Unnamed: 11_x (Chỉ giữ lại kiểu số)
        # pd.to_numeric với errors='coerce' sẽ biến các giá trị text thành NaN
        df_cleaned["Unnamed: 11_x"] = pd.to_numeric(df_cleaned["Unnamed: 11_x"], errors='coerce')
        
        # Sau đó ta xóa các dòng NaN vừa tạo ra ở cột Unnamed: 11_x
        df_cleaned = df_cleaned.dropna(subset=["Unnamed: 11_x"])

        # 4. Xuất file kết quả cuối cùng
        df_cleaned.to_excel(output_file, index=False)
        
        print(f"✅ ĐÃ HOÀN THÀNH LÀM SẠCH!")
        print(f"📊 Số dòng ban đầu: {len(df)}")
        print(f"📊 Số dòng sau khi lọc (Sạch 100%): {len(df_cleaned)}")
        print(f"🚀 File lưu tại: {os.path.abspath(output_file)}")
        
        # Hiển thị thử dữ liệu
        print("\nXem trước dữ liệu sau khi lọc:")
        print(df_cleaned[["Unnamed: 11_x", "Unnamed: 15_x"]].head())

    except Exception as e:
        print(f"❌ Lỗi: {e}")

# --- THỰC THI ---
file_input = "Ket_Qua_Merge_Cuoi_Cung.xlsx"
file_output = "Ket_Qua_Cuoi_Cung_Chuan.xlsx"

if os.path.exists(file_input):
    final_data_cleaning(file_input, file_output)
else:
    print(f"❌ Không tìm thấy file {file_input}. Vui lòng chạy bước Merge trước.")