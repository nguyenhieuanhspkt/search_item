import pandas as pd
import openpyxl
from tqdm import tqdm
import os
import re
import socket
import warnings
from datetime import datetime

# 1. Tắt cảnh báo
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# --- ĐIỀU CHỈNH REGEX: Khớp xx.xxx.01.xxxx hoặc xx.xxx.10.xxxx ---
# ^[^.]+ : Bắt đầu bằng cụm không có dấu chấm (vị trí 1)
# \.[^.]+ : Dấu chấm và cụm tiếp theo (vị trí 2)
# \.(01|10) : Dấu chấm và số 01 hoặc 10 (vị trí 3)
PATTERN_PHIEU = re.compile(r'^[^.]+\.[^.]+\.(01|10)\..*')

def get_base_path():
    path_coquan = r"D:\TaskApp_kiet\TaskApp\search_item2\search_item"
    path_onha = r"D:\TaskApp_pro\search_item"
    return path_coquan if os.path.exists(path_coquan) else path_onha

BASE_PATH = get_base_path()
HISTORY_PATH = os.path.join(BASE_PATH, "back_end", "History_data")
CURRENT_PATH = os.path.join(BASE_PATH, "back_end", "Current_data")
SPEC_FILE = os.path.join(CURRENT_PATH, "DM_vattu.xlsx") 
MASTER_DB_FILE = os.path.join(BASE_PATH, "back_end", "Master_Database.pkl")
MEILI_DATA_FILE = os.path.join(BASE_PATH, "back_end", "Data_For_Meili.xlsx")

def clean_number(value):
    if value is None or value == "": return 0.0
    if isinstance(value, (int, float)): return float(value)
    str_val = str(value).strip().replace(" ", "").replace("\xa0", "").replace(".", "")
    try: return float(str_val.replace(",", "."))
    except ValueError: return 0.0

def extract_contract_info(text):
    if not text or text == "None": return "Không rõ", "Nhập mua sắm"
    text_upper = text.upper()
    loai_nv = "Nhập mua sắm"
    if any(x in text_upper for x in ["THU HỒI", "ĐIỀU CHỈNH", "NHẬP LẠI", "CÂN ĐỐI", "MƯỢN"]):
        loai_nv = "Nội bộ/Thu hồi"
    patterns = [r'(?:HĐ|QĐ|SỐ|PO)[:\s]*([A-Z0-9\/\-\.]+)', r'([A-Z0-9]+\/[A-Z0-9\/\-\.]+)']
    so_hd = "Không rõ"
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            temp = match.group(1).strip().strip('()').strip('.')
            if len(temp) > 2:
                so_hd = temp
                break
    return so_hd, loai_nv

def load_specs():
    if not os.path.exists(SPEC_FILE): return pd.DataFrame()
    try:
        df_spec = pd.read_excel(SPEC_FILE)
        target_col = "Mã hiệu/Thông số kỹ thuật"
        if target_col not in df_spec.columns:
            found = [c for c in df_spec.columns if "thông số" in c.lower() or "mã hiệu" in c.lower()]
            if found: target_col = found[0]
        df_spec = df_spec[['Mã vật tư', target_col]]
        df_spec['Mã vật tư'] = df_spec['Mã vật tư'].astype(str).str.strip()
        return df_spec.rename(columns={target_col: 'Thông số kỹ thuật'})
    except: return pd.DataFrame()

def process_single_file(file_path, filename):
    year_label = "".join(filter(str.isdigit, filename))
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    ws = wb.active
    rows_data = []
    current_kho = "Chưa xác định"
    current_item = None
    
    for row in tqdm(ws.iter_rows(min_row=1), desc=f" > {filename}", leave=False):
        if not row or len(row) < 7: continue 

        col_a_val = row[0].value
        col_a_str = str(col_a_val) if col_a_val else ""
        
        if "Kho:" in col_a_str or "KHO" in col_a_str:
            temp_kho = col_a_str.replace("Kho:", "").strip()
            current_kho = "SKIP" if any(x in temp_kho.upper() for x in ["THAN", "DẦU", "DAU"]) else temp_kho
            continue
        if current_kho == "SKIP": continue

        if "Vật tư:" in col_a_str:
            clean_text = col_a_str.replace("Vật tư:", "").strip()
            parts = [p.strip() for p in re.split(r'\s+-\s+', clean_text)]
            if len(parts) >= 2:
                current_item = {"ma": parts[0], "ten": parts[1], "dvt": parts[2] if len(parts) > 2 else ""}
            continue
            
        if len(row) >= 9:
            sl_nhap = clean_number(row[6].value)
            val_col_b = str(row[1].value).strip() if row[1].value else ""
            
            # KIỂM TRA ĐIỀU KIỆN VỊ TRÍ THỨ 3
            if sl_nhap > 0 and PATTERN_PHIEU.match(val_col_b):
                ngay_nhap = col_a_val
                if not ngay_nhap or "Tổng cộng" in str(ngay_nhap): continue
                
                dien_giai = str(row[3].value) if row[3].value else ""
                so_hd, loai_nv = extract_contract_info(dien_giai)
                don_gia = clean_number(row[7].value)
                
                if current_item:
                    rows_data.append({
                        "id_raw": f"{current_item['ma']}_{val_col_b}_{ngay_nhap}",
                        "Năm": year_label,
                        "Kho": current_kho,
                        "Mã vật tư": str(current_item["ma"]).strip(),
                        "Tên vật tư (NXT)": current_item["ten"],
                        "Đơn vị tính": current_item["dvt"],
                        "Ngày Nhập": ngay_nhap,
                        "Số Phiếu (Cột B)": val_col_b,
                        "Đơn Giá Nhập": don_gia,
                        "Số Hợp Đồng/QĐ": so_hd,
                        "Diễn Giải": dien_giai
                    })
    wb.close()
    return rows_data

def tinh_gon_du_lieu(df, df_specs):
    df['Ngày Nhập'] = pd.to_datetime(df['Ngày Nhập'], errors='coerce')
    df = df.sort_values(by='Ngày Nhập', ascending=False)
    
    df_gon = df.groupby('Mã vật tư').agg({
        'Tên vật tư (NXT)': 'first',
        'Đơn Giá Nhập': 'first',
        'Đơn vị tính': 'first',
        'Số Phiếu (Cột B)': 'first',
        'Ngày Nhập': 'first',
        'Số Hợp Đồng/QĐ': lambda x: ' | '.join(set(str(i) for i in x if i != "Không rõ")),
        'Năm': 'first',
        'Kho': 'first',
        'Diễn Giải': 'first'
    }).reset_index()

    today = datetime.now()
    df_gon['Trên 12 tháng'] = df_gon['Ngày Nhập'].apply(
        lambda d: "Có" if not pd.isnull(d) and ((today.year - d.year) * 12 + (today.month - d.month)) > 12 else "Không"
    )

    if not df_specs.empty:
        df_gon = pd.merge(df_gon, df_specs, on='Mã vật tư', how='left')
    else:
        df_gon['Thông số kỹ thuật'] = ""

    df_gon['search_string'] = (
        df_gon['Mã vật tư'].astype(str) + " " + 
        df_gon['Tên vật tư (NXT)'].astype(str) + " " + 
        df_gon['Thông số kỹ thuật'].fillna("").astype(str) + " " +
        df_gon['Số Phiếu (Cột B)'].astype(str)
    )
    return df_gon

def main():
    df_specs = load_specs()
    all_data = []
    for path in [HISTORY_PATH, CURRENT_PATH]:
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith('.xlsx') and not f.startswith('~$')]
            for f in files:
                all_data.extend(process_single_file(os.path.join(path, f), f))

    if not all_data:
        print("❌ Không tìm thấy dòng dữ liệu nào khớp với vị trí thứ 3 là 01 hoặc 10!")
        return

    df_raw = pd.DataFrame(all_data)
    df_raw = df_raw.drop_duplicates(subset=['id_raw'], keep='last')
    df_raw.to_pickle(MASTER_DB_FILE)
    df_meili = tinh_gon_du_lieu(df_raw, df_specs)
    df_meili.to_excel(MEILI_DATA_FILE, index=False)
    print(f"✨ HOÀN THÀNH! Đã tìm thấy {len(df_meili)} mã vật tư khớp điều kiện.")

if __name__ == "__main__":
    main()