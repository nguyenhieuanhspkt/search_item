import pandas as pd
import openpyxl
from tqdm import tqdm
import os
import re
import socket
import warnings

# 1. Tắt cảnh báo
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def get_base_path():
    path_coquan = r"D:\TaskApp_kiet\TaskApp\search_item2\search_item"
    path_onha = r"D:\TaskApp_pro\search_item"
    hostname = socket.gethostname()
    return path_coquan if os.path.exists(path_coquan) else path_onha

BASE_PATH = get_base_path()
HISTORY_PATH = os.path.join(BASE_PATH, "back_end", "History_data")
CURRENT_PATH = os.path.join(BASE_PATH, "back_end", "Current_data")

# FILE QUAN TRỌNG: Chứa cột "Mã hiệu/Thông số kỹ thuật"
SPEC_FILE = os.path.join(CURRENT_PATH, "DM_vattu.xlsx") 

MASTER_DB_FILE = os.path.join(BASE_PATH, "back_end", "Master_Database.pkl")
MEILI_DATA_FILE = os.path.join(BASE_PATH, "back_end", "Data_For_Meili.xlsx")

# ======================================================
# HÀM BỔ SUNG: ĐỌC THÔNG SỐ KỸ THUẬT TỪ DANH MỤC GỐC
# ======================================================
def load_specs():
    print(f"🔍 Đang nạp thông số kỹ thuật từ: {os.path.basename(SPEC_FILE)}...")
    if not os.path.exists(SPEC_FILE):
        print("⚠️ Không tìm thấy file DM_vattu.xlsx, sẽ không có cột Thông số!")
        return pd.DataFrame()
    
    # Đọc file danh mục, chỉ lấy Mã vật tư và cột Thông số
    df_spec = pd.read_excel(SPEC_FILE)
    
    # Chuẩn hóa tên cột (Hiếu kiểm tra tên cột trong file Excel xem có đúng ko nhé)
    # Ở đây mình giả định cột đó tên là "Mã hiệu/Thông số kỹ thuật"
    target_col = "Mã hiệu/Thông số kỹ thuật"
    if target_col not in df_spec.columns:
        # Nếu ko thấy, thử tìm cột nào có chữ "Thông số"
        found = [c for c in df_spec.columns if "thông số" in c.lower() or "mã hiệu" in c.lower()]
        if found: target_col = found[0]

    df_spec = df_spec[['Mã vật tư', target_col]]
    df_spec['Mã vật tư'] = df_spec['Mã vật tư'].astype(str).str.strip()
    return df_spec.rename(columns={target_col: 'Thông số kỹ thuật'})

# ... (Giữ nguyên các hàm clean_number, extract_contract_info, process_single_file của Hiếu) ...

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

def process_single_file(file_path, filename):
    year_label = "".join(filter(str.isdigit, filename))
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    ws = wb.active
    rows_data = []
    current_kho = "Chưa xác định"
    current_item = None
    
    for row in tqdm(ws.iter_rows(min_row=1), desc=f" > {filename}", leave=False):
        # --- BƯỚC FIX LỖI: Kiểm tra độ dài dòng ---
        # Nếu dòng không đủ số cột (ít nhất 9 cột để lấy được index 8), ta bỏ qua hoặc xử lý riêng
        if not row or len(row) < 7: 
            continue 

        col_a = str(row[0].value) if row[0].value else ""
        
        # Xử lý các dòng tiêu đề Kho/Vật tư (thường nằm ở cột A)
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
            
        # Kiểm tra lại một lần nữa trước khi truy cập index 6, 7, 8
        if len(row) >= 9:
            sl_nhap = clean_number(row[6].value)
            if sl_nhap > 0:
                ngay_nhap = row[0].value
                if not ngay_nhap or "Tổng cộng" in str(ngay_nhap): continue
                
                dien_giai = str(row[3].value) if row[3].value else ""
                so_hd, loai_nv = extract_contract_info(dien_giai)
                don_gia = clean_number(row[7].value)
                
                if current_item:
                    rows_data.append({
                        "id_raw": f"{current_item['ma']}_{row[1].value}",
                        "Năm": year_label,
                        "Kho": current_kho,
                        "Mã vật tư": str(current_item["ma"]).strip(),
                        "Tên vật tư (NXT)": current_item["ten"],
                        "Đơn vị tính": current_item["dvt"],
                        "Ngày Nhập": ngay_nhap,
                        "Đơn Giá Nhập": don_gia,
                        "Số Hợp Đồng/QĐ": so_hd,
                        "Diễn Giải": dien_giai
                    })
                    
    wb.close()
    return rows_data

def tinh_gon_du_lieu(df, df_specs):
    print("🧹 Đang tinh gọn và HỢP NHẤT thông số kỹ thuật...")
    df['Ngày Nhập'] = pd.to_datetime(df['Ngày Nhập'], errors='coerce')
    df = df.sort_values(by='Ngày Nhập', ascending=False)
    
    # Gom nhóm
    df_gon = df.groupby('Mã vật tư').agg({
        'Tên vật tư (NXT)': 'first',
        'Đơn Giá Nhập': 'first',
        'Đơn vị tính': 'first',
        'Số Hợp Đồng/QĐ': lambda x: ' | '.join(set(str(i) for i in x if i != "Không rõ")),
        'Năm': 'first',
        'Kho': 'first',
        'Diễn Giải': 'first'
    }).reset_index()

    # --- BƯỚC QUAN TRỌNG: MERGE THÔNG SỐ TỪ FILE DANH MỤC ---
    if not df_specs.empty:
        df_gon = pd.merge(df_gon, df_specs, on='Mã vật tư', how='left')
    else:
        df_gon['Thông số kỹ thuật'] = ""

    # Tạo trường tìm kiếm tổng hợp (Search String) bao gồm cả Thông số
    df_gon['search_string'] = (
        df_gon['Mã vật tư'].astype(str) + " " + 
        df_gon['Tên vật tư (NXT)'].astype(str) + " " + 
        df_gon['Thông số kỹ thuật'].fillna("").astype(str) + " " +
        df_gon['Số Hợp Đồng/QĐ'].astype(str)
    )
    return df_gon

def main():
    # 1. Đọc thông số kỹ thuật trước
    df_specs = load_specs()

    # 2. Quét dữ liệu NXT
    all_data = []
    for path in [HISTORY_PATH, CURRENT_PATH]:
        if os.path.exists(path):
            for f in os.listdir(path):
                if f.endswith('.xlsx') and not f.startswith('~$'):
                    all_data.extend(process_single_file(os.path.join(path, f), f))

    if not all_data:
        print("❌ Không thấy dữ liệu!")
        return

    df_raw = pd.DataFrame(all_data)
    df_raw = df_raw.drop_duplicates(subset=['id_raw'], keep='last')
    df_raw.to_pickle(MASTER_DB_FILE)

    # 3. Tinh gọn và Merge cột thông số
    df_meili = tinh_gon_du_lieu(df_raw, df_specs)
    
    # 4. Xuất file
    df_meili.to_excel(MEILI_DATA_FILE, index=False)
    print(f"✨ HOÀN THÀNH! Đã gộp cột Thông số kỹ thuật thành công.")
    print(f"📊 Tổng số mã: {len(df_meili)}")

if __name__ == "__main__":
    main()