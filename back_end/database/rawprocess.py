import pandas as pd
import openpyxl
from tqdm import tqdm
import os
import re
import socket
import warnings

# 1. Tắt cảnh báo định dạng của openpyxl để Console sạch sẽ
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# ======================================================
# KIỂM TRA MÔI TRƯỜNG VÀ CẤU HÌNH ĐƯỜNG DẪN
# ======================================================
def get_base_path():
    path_coquan = r"D:\TaskApp_kiet\TaskApp\search_item2\search_item"
    path_onha = r"D:\TaskApp_pro\search_item"
    
    hostname = socket.gethostname()
    
    if os.path.exists(path_coquan):
        print(f"📌 Đang chạy tại: CO QUAN ({hostname})")
        return path_coquan
    else:
        print(f"📌 Đang chạy tại: NHA ({hostname})")
        return path_onha

BASE_PATH = get_base_path()

# Cấu hình đường dẫn chi tiết
HISTORY_PATH = os.path.join(BASE_PATH, "back_end", "History_data")
CURRENT_PATH = os.path.join(BASE_PATH, "back_end", "Current_data")
SPEC_FILE = os.path.join(CURRENT_PATH, "DM_vattu.xlsx")
MASTER_DB_FILE = os.path.join(BASE_PATH, "back_end", "Master_Database.pkl")
# File đã tinh gọn để nạp vào Meilisearch
MEILI_DATA_FILE = os.path.join(BASE_PATH, "back_end", "Data_For_Meili.xlsx") 

# ======================================================
# CÁC HÀM XỬ LÝ LOGIC
# ======================================================

def clean_number(value):
    if value is None or value == "": return 0.0
    if isinstance(value, (int, float)): return float(value)
    str_val = str(value).strip().replace(" ", "").replace("\xa0", "").replace(".", "")
    try:
        return float(str_val.replace(",", "."))
    except ValueError:
        return 0.0

def extract_contract_info(text):
    if not text or text == "None": return "Không rõ", "Nhập mua sắm"
    text_upper = text.upper()
    loai_nv = "Nhập mua sắm"
    if any(x in text_upper for x in ["THU HỒI", "ĐIỀU CHỈNH", "NHẬP LẠI", "CÂN ĐỐI", "MƯỢN"]):
        loai_nv = "Nội bộ/Thu hồi"
        if "THU HỒI" in text_upper: loai_nv = "Nhập thu hồi"
    
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

def process_single_file(file_path, filename):
    year_label = "".join(filter(str.isdigit, filename))
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    ws = wb.active
    rows_data = []
    current_kho = "Chưa xác định"
    current_item = None
    
    for row in tqdm(ws.iter_rows(min_row=1), desc=f" > {filename}", leave=False):
        col_a = str(row[0].value) if row[0].value else ""
        if "Kho:" in col_a or "KHO" in col_a:
            temp_kho = col_a.replace("Kho:", "").strip()
            current_kho = "SKIP" if any(x in temp_kho.upper() for x in ["THAN", "DẦU", "DAU"]) else temp_kho
            continue
        if current_kho == "SKIP": continue

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
                    "id_raw": f"{current_item['ma']}_{row[1].value}", # Tạo ID tạm để khử trùng
                    "Năm": year_label,
                    "Kho": current_kho,
                    "Mã vật tư": str(current_item["ma"]).strip(),
                    "Tên vật tư (NXT)": current_item["ten"],
                    "Đơn vị tính": current_item["dvt"],
                    "Ngày Nhập": ngay_nhap,
                    "Đơn Giá Nhập": don_gia,
                    "Số Hợp Đồng/QĐ": so_hd,
                    "Loại Nghiệp Vụ": loai_nv,
                    "Diễn Giải": dien_giai
                })
    wb.close()
    return rows_data

def tinh_gon_du_lieu(df):
    print("🧹 Đang tinh gọn dữ liệu cho Meilisearch...")
    # Sắp xếp để lấy ngày mới nhất lên trên
    df['Ngày Nhập'] = pd.to_datetime(df['Ngày Nhập'], errors='coerce')
    df = df.sort_values(by='Ngày Nhập', ascending=False)
    
    # Gom nhóm theo Mã vật tư
    df_gon = df.groupby('Mã vật tư').agg({
        'Tên vật tư (NXT)': 'first',
        'Đơn Giá Nhập': 'first',
        'Đơn vị tính': 'first',
        'Số Hợp Đồng/QĐ': lambda x: ' | '.join(set(str(i) for i in x if i != "Không rõ")),
        'Năm': 'first',
        'Kho': 'first',
        'Diễn Giải': 'first'
    }).reset_index()

    # Tạo trường tìm kiếm tổng hợp (Search String)
    df_gon['search_string'] = (
        df_gon['Mã vật tư'].astype(str) + " " + 
        df_gon['Tên vật tư (NXT)'].astype(str) + " " + 
        df_gon['Số Hợp Đồng/QĐ'].astype(str)
    )
    return df_gon

# ======================================================
# HÀM CHÍNH
# ======================================================
def main():
    # 1. Quét file History
    all_data = []
    if os.path.exists(HISTORY_PATH):
        for f in [f for f in os.listdir(HISTORY_PATH) if f.endswith('.xlsx')]:
            all_data.extend(process_single_file(os.path.join(HISTORY_PATH, f), f))

    # 2. Quét file Current
    if os.path.exists(CURRENT_PATH):
        for f in [f for f in os.listdir(CURRENT_PATH) if f.startswith('017_') and f.endswith('.xlsx')]:
            all_data.extend(process_single_file(os.path.join(CURRENT_PATH, f), f))

    if not all_data:
        print("❌ Không tìm thấy dữ liệu nào!")
        return

    df_raw = pd.DataFrame(all_data)
    
    # 3. Khử trùng bản ghi thô
    df_raw = df_raw.drop_duplicates(subset=['id_raw'], keep='last')
    df_raw.to_pickle(MASTER_DB_FILE)

    # 4. Tinh gọn để làm App Search
    df_meili = tinh_gon_du_lieu(df_raw)
    
    # 5. Xuất kết quả
    df_meili.to_excel(MEILI_DATA_FILE, index=False)
    
    print(f"✨ HOÀN THÀNH!")
    print(f"📂 Master DB: {MASTER_DB_FILE}")
    print(f"🚀 File nạp Meilisearch: {MEILI_DATA_FILE}")
    print(f"📊 Tổng số mã vật tư duy nhất: {len(df_meili)}")

if __name__ == "__main__":
    main()