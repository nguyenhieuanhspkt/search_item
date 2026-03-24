import pandas as pd
import openpyxl
from tqdm import tqdm
import os
import re

# --- CẤU HÌNH ĐƯỜNG DẪN ---
HISTORY_PATH = r"D:\TaskApp_pro\search_item\back_end\History_data"
CURRENT_PATH = r"D:\TaskApp_pro\search_item\back_end\Current_data"
SPEC_FILE = os.path.join(CURRENT_PATH, "DM_vattu.xlsx")
MASTER_DB_FILE = r"D:\TaskApp_pro\search_item\back_end\Master_Database.pkl"
OUTPUT_EXCEL = r"D:\TaskApp_pro\search_item\back_end\Data_Final_Search.xlsx"

def clean_number(value):
    if value is None or value == "": return 0.0
    if isinstance(value, (int, float)): return float(value)
    str_val = str(value).strip().replace(" ", "").replace("\xa0", "").replace(".", "")
    try:
        return float(str_val.replace(",", "."))
    except ValueError:
        return 0.0

def extract_contract_info(text):
    """Bóc tách HĐ, QĐ hoặc ghi chú Thu hồi từ Diễn giải"""
    if not text or text == "None": return "Không rõ", "Nhập mua sắm"
    
    text_upper = text.upper()
    
    # 1. Phân loại nghiệp vụ trước
    loai_nv = "Nhập mua sắm"
    if any(x in text_upper for x in ["THU HỒI", "ĐIỀU CHỈNH", "NHẬP LẠI", "CÂN ĐỐI", "MƯỢN"]):
        loai_nv = "Nội bộ/Thu hồi"
        if "THU HỒI" in text_upper: loai_nv = "Nhập thu hồi"
    
    # 2. Tìm số HĐ/QĐ (Không bắt buộc có .01.)
    # Tìm sau các từ khóa HĐ, QĐ, Số, PO hoặc chuỗi có gạch chéo /
    patterns = [
        r'(?:HĐ|QĐ|SỐ|PO)[:\s]*([A-Z0-9\/\-\.]+)', 
        r'([A-Z0-9]+\/[A-Z0-9\/\-\.]+)' # Ưu tiên chuỗi có dấu /
    ]
    
    so_hd = "Không rõ"
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            temp = match.group(1).strip().strip('()').strip('.')
            if len(temp) > 2: # Tránh lấy số lẻ tẻ
                so_hd = temp
                break
                
    return so_hd, loai_nv

def process_single_file(file_path, filename):
    year_label = "".join(filter(str.isdigit, filename))
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    ws = wb.active
    
    rows_data = []
    current_kho = "Chưa xác định"
    current_item = None
    
    for row in tqdm(ws.iter_rows(min_row=1), desc=f" > {filename}", leave=False):
        col_a = str(row[0].value) if row[0].value else ""
        
        # Lọc Kho Than/Dầu
        if "Kho:" in col_a or "KHO" in col_a:
            temp_kho = col_a.replace("Kho:", "").strip()
            current_kho = "SKIP" if any(x in temp_kho.upper() for x in ["THAN", "DẦU", "DAU"]) else temp_kho
            continue
        if current_kho == "SKIP": continue

        # Tách tên VT (L-Ascorbic)
        if "Vật tư:" in col_a:
            clean_text = col_a.replace("Vật tư:", "").strip()
            parts = [p.strip() for p in re.split(r'\s+-\s+', clean_text)]
            if len(parts) >= 2:
                current_item = {"ma": parts[0], "ten": parts[1], "dvt": parts[2] if len(parts) > 2 else ""}
            continue
            
        sl_nhap = clean_number(row[6].value)
        if sl_nhap > 0:
            ngay_nhap = row[0].value
            if not ngay_nhap or "Tổng cộng" in str(ngay_nhap): continue
            
            dien_giai = str(row[3].value) if row[3].value else ""
            so_hd, loai_nv = extract_contract_info(dien_giai)
            
            don_gia = clean_number(row[7].value)
            thanh_tien = clean_number(row[8].value)
            if don_gia == 0 and thanh_tien > 0: don_gia = thanh_tien / sl_nhap

            if current_item:
                rows_data.append({
                    "Năm": year_label,
                    "Kho": current_kho,
                    "Mã vật tư": current_item["ma"],
                    "Tên vật tư (NXT)": current_item["ten"],
                    "Đơn vị tính": current_item["dvt"],
                    "Ngày Nhập": ngay_nhap,
                    "Đơn Giá Nhập": don_gia,
                    "Số Lượng Nhập": sl_nhap,
                    "Số Hợp Đồng/QĐ": so_hd,
                    "Loại Nghiệp Vụ": loai_nv,
                    "Diễn Giải": dien_giai,
                    "Chứng Từ Kho": row[1].value
                })
    wb.close()
    return rows_data

def main():
    # 1. Nạp History
    if not os.path.exists(MASTER_DB_FILE):
        print("🚀 Khởi tạo Master Database...")
        all_hist = []
        for f in [f for f in os.listdir(HISTORY_PATH) if f.endswith('.xlsx')]:
            all_hist.extend(process_single_file(os.path.join(HISTORY_PATH, f), f))
        df_master = pd.DataFrame(all_hist)
    else:
        df_master = pd.read_pickle(MASTER_DB_FILE)

    # 2. Nạp Current
    all_curr = []
    for f in [f for f in os.listdir(CURRENT_PATH) if f.startswith('017_') and f.endswith('.xlsx')]:
        all_curr.extend(process_single_file(os.path.join(CURRENT_PATH, f), f))
    df_curr = pd.DataFrame(all_curr)

    # 3. Gộp & Khử trùng
    df_combined = pd.concat([df_master, df_curr], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['Ngày Nhập', 'Chứng Từ Kho', 'Mã vật tư', 'Số Lượng Nhập'], keep='last')
    df_combined.to_pickle(MASTER_DB_FILE)

    # 4. Merge Specs
    if os.path.exists(SPEC_FILE):
        df_specs = pd.read_excel(SPEC_FILE)
        df_specs.columns = [str(col).strip() for col in df_specs.columns]
        df_specs = df_specs.drop_duplicates(subset=['Mã vật tư'])
        df_combined['Mã vật tư'] = df_combined['Mã vật tư'].astype(str).str.strip()
        df_specs['Mã vật tư'] = df_specs['Mã vật tư'].astype(str).str.strip()
        df_final = pd.merge(df_combined, df_specs, on='Mã vật tư', how='left')
    else:
        df_final = df_combined

    # 5. Xuất Excel
    df_final.to_excel(OUTPUT_EXCEL, index=False)
    print(f"✨ XONG! Đã bóc tách HĐ/QĐ và phân loại nghiệp vụ.")

if __name__ == "__main__":
    main()