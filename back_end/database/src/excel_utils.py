import pandas as pd
import os

def get_clean_df(file_path, sheet_name_keyword, header_keyword="Mã hạng mục"):
    """Đọc, tìm header và điền đầy (ffill) mã hạng mục."""
    try:
        xl = pd.ExcelFile(file_path)
        actual_sheet_name = next((s for s in xl.sheet_names if sheet_name_keyword in s), None)
        if not actual_sheet_name: return None

        df_temp = pd.read_excel(file_path, sheet_name=actual_sheet_name, header=None)
        header_row_index = 0
        for i, row in df_temp.iterrows():
            row_str = row.astype(str).values
            if any(header_keyword in s for s in row_str) or any("hạng mục" in s.lower() for s in row_str):
                header_row_index = i
                break
        
        df = pd.read_excel(file_path, sheet_name=actual_sheet_name, header=header_row_index)
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]

        # Fill Down mã hạng mục
        col_ma_hm = df.columns[0] 
        df[col_ma_hm] = df[col_ma_hm].replace(r'^\s*$', pd.NA, regex=True).ffill()
        
        return df, actual_sheet_name
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return None, None
def user_select_column(df, message="Hãy chọn cột"):
    """Hiển thị danh sách cột theo lưới và tự động Preview dữ liệu."""
    cols = df.columns.tolist()
    print(f"\n{'='*70}")
    print(f"🔍 {message.upper()}")
    print(f"{'='*70}")

    # 1. Lọc nhanh (Search)
    search = input("👉 Nhập từ khóa để lọc (Ví dụ: 'Mã', 'Giá', 'VT'...) hoặc Enter để hiện tất cả: ").strip().lower()
    
    filtered_indices = [i for i, col in enumerate(cols) if search in str(col).lower()] if search else list(range(len(cols)))

    # 2. Hiển thị Grid View (3 cột/dòng)
    print(f"\n--- DANH SÁCH {len(filtered_indices)} CỘT TÌM THẤY ---")
    row_str = ""
    for count, idx in enumerate(filtered_indices):
        col_name = str(cols[idx])[:18]
        item = f"[{idx:3}] {col_name:<18}"
        row_str += item + " | "
        if (count + 1) % 3 == 0:
            print(row_str)
            row_str = ""
    if row_str: print(row_str)

    # 3. Vòng lặp chọn và Preview
    while True:
        try:
            choice = input(f"\n👉 Nhập số thứ tự (0-{len(cols)-1}) để CHỌN (hoặc 'q' để tìm lại): ").lower()
            if choice == 'q': return user_select_column(df, message) # Quay lại bước lọc
            
            idx = int(choice)
            if 0 <= idx < len(cols):
                # --- ĐÂY LÀ PHẦN PREVIEW TỰ ĐỘNG ---
                print(f"\n👀 ĐANG XEM THỬ DỮ LIỆU CỘT [{cols[idx]}]:")
                print("-" * 40)
                # Lấy 5 dòng đầu, bỏ qua NaN để Hiếu thấy được nội dung thực
                preview_data = df[cols[idx]].dropna().head(5).tolist()
                if not preview_data:
                    print(" (Cột này toàn ô trống hoặc NaN) ")
                for val in preview_data:
                    print(f"  > {val}")
                print("-" * 40)
                
                confirm = input(f"✅ Đúng cột này chưa Hiếu? (y/n): ").lower()
                if confirm == 'y' or confirm == '':
                    return cols[idx]
            else:
                print("⚠️ Số thứ tự không tồn tại!")
        except ValueError:
            print("⚠️ Vui lòng nhập số thứ tự cột.")
def save_to_excel(dict_dfs, output_path, has_mark_row=False):
    """Lưu dictionary các DataFrame thành các sheet Excel."""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in dict_dfs.items():
            if df is not None:
                if has_mark_row:
                    # Chèn dòng trống ở đầu để đánh dấu 'x'
                    df_final = pd.concat([pd.DataFrame([[""] * len(df.columns)], columns=df.columns), df], ignore_index=True)
                    df_final.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)