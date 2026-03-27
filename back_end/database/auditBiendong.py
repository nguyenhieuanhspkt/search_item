import pandas as pd
import numpy as np
import os
from thefuzz import fuzz # Thư viện so sánh độ giống nhau của chuỗi

def process_advanced_audit():
    # --- ĐƯỜNG DẪN (GIỮ NGUYÊN) ---
    input_path = r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\Năm 2026\Thẩm định 109_hieuna_3\2026-03-25-Ý kiến thẩm định.xlsx"
    output_dir = r"D:\TaskApp_kiet\TaskApp\search_item2\search_item\back_end\ai_audit_system\data\processed"
    output_path = os.path.join(output_dir, "Ket_qua_Tham_dinh_Nang_cao.xlsx")

    df = pd.read_excel(input_path, sheet_name="Sheet1_data")
    
    # Chuẩn hóa dữ liệu số
    price_cols = df.iloc[:, 16:30].apply(pd.to_numeric, errors='coerce')
    don_gia_dx = pd.to_numeric(df.iloc[:, 4], errors='coerce') # Cột E
    ten_vattu = df.iloc[:, 1].astype(str) # Giả định cột B (index 1) là tên/thông số

    # --- 1. PHÁT HIỆN GIÁ NỔI TRỘI (Z-SCORE) ---
    row_mean = price_cols.mean(axis=1)
    row_std = price_cols.std(axis=1, ddof=1)
    
    # Tính mức độ lệch của giá đề xuất so với trung bình báo giá
    # Công thức: (Giá DX - Trung bình BG) / Độ lệch chuẩn
    df['Z_Score_Noi_Troi'] = ((don_gia_dx - row_mean) / row_std).fillna(0)
    df['Canh_bao_Noi_troi'] = df['Z_Score_Noi_Troi'].apply(lambda x: "RẤT CAO" if x > 2 else ("CAO" if x > 1 else "Bình thường"))

    # --- 2. SO SÁNH THÔNG SỐ GIỐNG NHAU - GIÁ KHÁC NHAU ---
    df['Giong_nhau_nhung_gia_khac'] = ""
    
    # Chạy vòng lặp so sánh từng cặp (Lưu ý: Nếu file > 1000 dòng sẽ hơi chậm)
    for i in range(len(df)):
        current_name = ten_vattu[i]
        current_price = don_gia_dx[i]
        
        for j in range(i + 1, min(i + 50, len(df))): # So sánh với 50 dòng kế tiếp để tối ưu tốc độ
            target_name = ten_vattu[j]
            target_price = don_gia_dx[j]
            
            # Tính độ giống nhau của tên/thông số (0-100)
            similarity = fuzz.token_sort_ratio(current_name, target_name)
            
            if similarity > 85: # Nếu giống nhau trên 85%
                price_diff = abs(current_price - target_price) / max(current_price, 1)
                if price_diff > 0.1: # Nhưng giá lệch trên 10%
                    msg = f"Giống dòng {j+1} ({similarity}%). Lệch giá: {price_diff:.1%}"
                    df.at[i, 'Giong_nhau_nhung_gia_khac'] = msg
                    break

    # --- 3. XUẤT FILE ---
    df.to_excel(output_path, index=False)
    print(f"✨ Đã xuất báo cáo thẩm định nâng cao tại: {output_path}")

if __name__ == "__main__":
    process_advanced_audit()