import pandas as pd
import numpy as np
import os

def process_comprehensive_audit(input_file, output_file):
    try:
        if not os.path.exists(input_file):
            print(f"❌ Không tìm thấy file: {input_file}")
            return

        df = pd.read_excel(input_file)
        
        new_columns = [
            "Mã hạng mục", "Tên Vật tư", "ĐVT", "KHỐI LƯỢNG", 
            "ĐƠN GIÁ", "ĐƠN GIÁ KIỂM TRA", "THÀNH TIỀN TRÌNH DỰ TOÁN", 
            "MÃ GIÁ", "STT2", "Mã giá", "Thông số kỹ thuật điều chỉnh (KTAT)", 
            "ĐVT2", "HXS/XX", "Đơn giá", "Thuế", "Cơ sở lập dự toán", 
            "Đơn giá AH", "Đơn giá TC", "Đơn giá Vimico", "Đơn giá Howden", 
            "Thành Công", "Đại Phát", "Huy Minh", "Thiên An", 
            "Delta", "DTL", "PS", "Asean", "Hải Phòng", "Thăng Long", 
            "số cơ sở đơn giá"
        ]

        if len(df.columns) >= len(new_columns):
            df = df.iloc[:, :len(new_columns)]
            df.columns = new_columns
        else:
            print("⚠️ Số lượng cột không khớp!")
            return

        # --- BƯỚC XỬ LÝ QUAN TRỌNG CHO LỖI XUỐNG DÒNG ---
        # 1. Chuyển về string
        # 2. Thay thế ký tự xuống dòng (\n hoặc \r) bằng khoảng trắng
        # 3. Xóa khoảng trắng thừa ở đầu/cuối và thay 2 khoảng trắng bằng 1 khoảng trắng
        df["Tên Vật tư"] = (df["Tên Vật tư"]
                            .astype(str)
                            .str.replace(r'\r+|\n+', ' ', regex=True) # Xử lý lỗi xuống dòng
                            .str.replace(r'\s+', ' ', regex=True)     # Xử lý lỗi nhiều dấu cách
                            .str.strip())
        # -----------------------------------------------

        vendor_cols = new_columns[16:30] 
        for col in vendor_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # --- SHEET 1: TỔNG HỢP ---
        agg_rules = {col: 'first' for col in df.columns if col != "Tên Vật tư"}
        agg_rules["KHỐI LƯỢNG"] = 'sum'
        df_summary = df.groupby("Tên Vật tư", as_index=False).agg(agg_rules)
        df_summary = df_summary[new_columns]

        # --- SHEET 2: CẢNH BÁO ---
        df_audit = df_summary.copy()
        df_audit['Gia_Min'] = df_audit[vendor_cols].min(axis=1)
        df_audit['Gia_Max'] = df_audit[vendor_cols].max(axis=1)
        df_audit['Ty_Le_Lech'] = df_audit['Gia_Max'] / df_audit['Gia_Min']
        df_audit['So_Nha_Thau_Co_Gia'] = df_audit[vendor_cols].notna().sum(axis=1)

        crit1 = (df_audit["số cơ sở đơn giá"] <= 1)
        crit2 = (df_audit['Ty_Le_Lech'] > 1.5)
        crit3 = (df_audit['So_Nha_Thau_Co_Gia'] == 1)
        
        df_anomalies = df_audit[crit1 | crit2 | crit3].copy()
        
        def detect_reason(row):
            reasons = []
            if row["số cơ sở đơn giá"] <= 1: reasons.append("Ít cơ sở đơn giá")
            if row['Ty_Le_Lech'] > 1.5: reasons.append(f"Chênh lệch cao ({round(row['Ty_Le_Lech'],2)} lần)")
            if row['So_Nha_Thau_Co_Gia'] == 1: reasons.append("Chỉ 1 nhà thầu báo giá")
            return " + ".join(reasons)

        if not df_anomalies.empty:
            df_anomalies['LÝ DO BẤT THƯỜNG'] = df_anomalies.apply(detect_reason, axis=1)

        # --- SHEET 3: NHÀ THẦU ---
        vendor_stats = []
        total_items = len(df_summary)
        for v in vendor_cols:
            count_bid = df_summary[v].notna().sum()
            is_min = (df_summary[v] == df_audit['Gia_Min']) & (df_summary[v].notna())
            win_min = is_min.sum()
            vendor_stats.append({
                'Nhà Thầu': v,
                'Số mục tham gia': count_bid,
                '% Phủ sóng danh mục': f"{round((count_bid/total_items)*100, 2)}%" if total_items > 0 else "0%",
                'Số mục đạt giá thấp nhất': win_min,
                '% Hiệu quả (Rẻ nhất/Báo)': f"{round((win_min/count_bid)*100, 2)}%" if count_bid > 0 else "0%"
            })
        df_vendors = pd.DataFrame(vendor_stats)

        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            df_summary.to_excel(writer, sheet_name='1. Tong Hop Data', index=False)
            df_anomalies.to_excel(writer, sheet_name='2. Canh Bao Bat Thuong', index=False)
            df_vendors.to_excel(writer, sheet_name='3. Danh Gia Nha Thau', index=False)

        print(f"✅ HOÀN THÀNH! Đã xử lý lỗi xuống dòng và gộp dữ liệu.")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    process_comprehensive_audit("Ket_Qua_Cuoi_Cung_Chuan.xlsx", "Bao_Cao_Phan_Tich_Chuyen_Sau.xlsx")