import pandas as pd
import re

# --- CÁC HÀM CƠ BẢN (STEP 1 - 3) ---
def step_1_to_3_load_data(file_1_path, file_2_path):
    """
    Nạp và chuẩn hóa tên cột dựa trên tọa độ Index chính xác:
    - df3 (S1): D (TVT), M (DG - Index 12), S (Mã ERP_TTS1 - Index 18)
    - df4 (ERP): B (TVT), C (DG), D (DVT), J (History), K (Over1year), L (TSKT)
    """
    print(f"📖 Đang nạp dữ liệu từ các File...")
    df1 = pd.read_excel(file_1_path, sheet_name="PL1.5 DT VẬT TƯ TM")
    df2 = pd.read_excel(file_1_path, sheet_name="Cơ sở giá")
    df4 = pd.read_excel(file_1_path, sheet_name="ERP")
    df3 = pd.read_excel(file_2_path, sheet_name="PL1.5 DT VẬT TƯ TM")

    # --- XỬ LÝ DF3 (Kho Trung tu S1) ---
    mapping_df3 = {
        df3.columns[3]: 'TVT',            # Cột D
        df3.columns[12]: 'DG',            # Cột M (Index 12)
        df3.columns[18]: 'Ma_ERP_TTS1'    # Cột S (Index 18)
    }
    df3.rename(columns=mapping_df3, inplace=True)
    
    # --- XỬ LÝ DF4 (Kho ERP 20k dòng) ---
    mapping_df4 = {
        df4.columns[1]: 'TVT_Goc',     # Cột B
        df4.columns[2]: 'DG',          # Cột C
        df4.columns[3]: 'DVT',         # Cột D
        df4.columns[9]: 'history',      # Cột J (Index 9)
        df4.columns[10]: 'over1year',   # Cột K (Index 10)
        df4.columns[11]: 'TSKT'         # Cột L (Index 11)
    }
    df4.rename(columns=mapping_df4, inplace=True)

    # Tạo cột TVT tổng hợp cho df4 (Tên + Thông số)
    df4['TVT'] = df4['TVT_Goc'].astype(str).str.strip() + " " + df4['TSKT'].fillna("").astype(str).str.strip()
    df4['TVT'] = df4['TVT'].str.replace(r'\s+', ' ', regex=True).str.strip()

    print(f"✅ Đã chuẩn hóa df3 (kèm Ma_ERP_TTS1) và df4 (kèm History, Over1year).")
    return df1, df2, df3, df4

# --- STEP 4 & 5: XỬ LÝ DF1 + POPULATE DOWN MÃ HM ---

def step_4_and_5_process_df1(df1):
    df = df1.copy()
    
    # 1. Populate Down Mã HM (Cột B - index 1)
    df.iloc[:, 1] = df.iloc[:, 1].ffill()
    
    # 2. Cắt lấy vùng dữ liệu (Hàng 12 trở đi, các cột B-D, F, L, O, R)
    target_indices = [1, 2, 3, 5, 11, 14, 17]
    df_processed = df.iloc[10:, target_indices].copy()
    df_processed.columns = ['Mã HM', 'TVT', 'DVT', 'KL', 'DG', 'TT', 'MG']
    
    # 3. Ép kiểu số cho các cột tính toán để lọc chính xác
    df_processed['TT'] = pd.to_numeric(df_processed['TT'], errors='coerce')
    df_processed['KL'] = pd.to_numeric(df_processed['KL'], errors='coerce')
    df_processed['DG'] = pd.to_numeric(df_processed['DG'], errors='coerce')

    # --- MỤC TIÊU QUAN TRỌNG: CHỈ LẤY DÒNG CÓ THÀNH TIỀN KHÁC 0 ---
    # Loại bỏ các dòng TT bằng 0, NaN hoặc trống
    df_processed = df_processed[
        (df_processed['TT'].notna()) & 
        (df_processed['TT'] != 0)
    ].copy()
    
    return df_processed.reset_index(drop=True)

def clean_text_vinh_tan(text):
    if pd.isna(text): return ""
    t = str(text)
    t = re.sub(r'[\r\n\t]+', ' ', t)
    return ' '.join(t.split()).strip().upper()

def step_6_process_df2(df2):
    """
    Step 6: Chuẩn hóa bảng Cơ sở giá (df2)
    - Đổi tên 8 cột đầu theo danh mục nghiệp vụ.
    - Lấy text tại hàng 2 (index 0 của df) làm tên cho các cột còn lại (I -> V).
    - Loại bỏ hàng tiêu đề cũ để bắt đầu lấy dữ liệu từ hàng thực tế.
    """
    # 1. Định nghĩa 8 tên cột đầu tiên (A -> H)
    new_names = ['STT', 'MG', 'TVT', 'DVT', 'HSX', 'DG', 'TAX', 'Price_base']
    
    # 2. Lấy tên các cột còn lại từ hàng đầu tiên của df (tương ứng hàng 2 trong Excel)
    # Chúng ta lấy từ cột thứ 9 (index 8) trở đi
    remaining_cols = df2.iloc[0, 8:].astype(str).tolist() 
    
    # 3. Hợp nhất danh sách tên cột
    all_columns = new_names + remaining_cols
    
    # Gán lại tên cột cho DataFrame
    df2.columns = all_columns
    
    # 4. Loại bỏ hàng chứa tiêu đề (hàng index 0) và reset index
    # Dữ liệu thực tế sẽ bắt đầu từ dòng này trở đi
    df2_processed = df2.iloc[1:].reset_index(drop=True)
    
    # Đảm bảo mã MG được làm sạch (xóa khoảng trắng) để chuẩn bị Merge ở Chặng 1
    df2_processed['MG'] = df2_processed['MG'].astype(str).str.strip()
    
    return df2_processed

def process_phase_1_analytics(df1, df2):
    # 1. Làm sạch TVT
    df1['TVT_clean'] = df1['TVT'].apply(clean_text_vinh_tan)
    
    # 2. Chuẩn hóa MG
    df1['MG'] = df1['MG'].astype(str).str.strip()
    df2['MG'] = df2['MG'].astype(str).str.strip()

    # 3. Bóc tách bất thường giá (Vấn đề 1)
    price_variance = df1.groupby('TVT_clean')['DG'].nunique()
    anomaly_list = price_variance[price_variance > 1].index.tolist()
    df_anomalies = df1[df1['TVT_clean'].isin(anomaly_list)].sort_values(by='TVT_clean')

    # 4. Hợp nhất và Aggregation (Vấn đề 2)
    df2_unique_ref = df2.drop_duplicates(subset=['MG'], keep='first')
    df_merged = pd.merge(df1, df2_unique_ref, on='MG', how='left', suffixes=('', '_ref'))

    # Groupby theo MG để cộng dồn KL và TT
    df_unique_final = df_merged.groupby('MG').agg({
        'Mã HM': 'first',
        'TVT': 'first',
        'TVT_clean': 'first',
        'DVT': 'first',
        'KL': 'sum',            # Cộng dồn KL của các dòng trùng MG
        'DG': 'max',            # Giữ đơn giá cao nhất
        'TT': 'sum',            # Cộng dồn TT của các dòng trùng MG
        'HSX': 'first',
        'Price_base': 'first'
    }).reset_index()
    
    # Kiểm tra lại một lần nữa sau khi sum, chỉ lấy TT > 0
    df_unique_final = df_unique_final[df_unique_final['TT'] > 0]

    return df_anomalies, df_unique_final
from rapidfuzz import fuzz

def smart_vertical_grouping(df_unique):
    """
    Tiền xử lý Chặng 2 Nâng cao:
    1. Phát hiện trùng tên (Score 100) nhưng KHÁC đơn giá -> Xuất báo cáo.
    2. Gộp trùng tên (Score 100) và CÙNG đơn giá -> Cộng dồn KL.
    3. Sắp xếp các cặp gần giống (Fuzzy) nằm cạnh nhau.
    """
    print("🧠 Đang thực hiện Gộp thông minh và Kiểm tra bất thường giá...")

    # --- BƯỚC 1: TÌM BẤT THƯỜNG GIÁ (TRÙNG TÊN KHÁC GIÁ) ---
    # Đếm số lượng đơn giá duy nhất cho mỗi TVT_clean
    price_check = df_unique.groupby('TVT_clean')['DG'].nunique()
    anomaly_names = price_check[price_check > 1].index.tolist()
    
    # Trích xuất các dòng bị lỗi giá để đưa vào báo cáo
    df_anomalies = df_unique[df_unique['TVT_clean'].isin(anomaly_names)].sort_values(by='TVT_clean')

    # --- BƯỚC 2: GỘP DỮ LIỆU (CHỈ GỘP KHI CÙNG TÊN & CÙNG GIÁ) ---
    # Nhóm theo cả Tên và Đơn giá để đảm bảo không gộp nhầm các dòng sai giá
    df_smart_grouped = df_unique.groupby(['TVT_clean', 'DG']).agg({
        'Mã HM': 'first',
        'MG': 'first',
        'TVT': 'first',
        'DVT': 'first',
        'KL': 'sum',
        'TT': 'sum',
        'HSX': 'first',
        'Price_base': 'first'
    }).reset_index()

    # --- BƯỚC 3: SẮP XẾP HÀNG DỌC (FUZZY MATCH) ---
    df_smart_grouped['Group_ID'] = df_smart_grouped.index
    tvt_list = df_smart_grouped['TVT_clean'].tolist()
    processed_indices = set()

    for i in range(len(tvt_list)):
        if i in processed_indices: continue
        for j in range(i + 1, len(tvt_list)):
            if j in processed_indices: continue
            
            score = fuzz.token_sort_ratio(tvt_list[i], tvt_list[j])
            if score >= 85: # Các cặp gần giống
                df_smart_grouped.at[j, 'Group_ID'] = df_smart_grouped.at[i, 'Group_ID']
                processed_indices.add(j)

    df_final = df_smart_grouped.sort_values(by=['Group_ID', 'TVT_clean']).copy()
    
    return df_final, df_anomalies
def validate_financials(df_raw, df_final):
    """Hàm riêng để kiểm tra tổng tiền không bị thất thoát"""
    total_raw = df_raw[df_raw['TT'] > 0]['TT'].sum()
    total_final = df_final['TT'].sum()
    diff = abs(total_raw - total_final)
    return diff, total_raw, total_final


from rapidfuzz import process, fuzz

def step_0_split_by_source(df_input):
    """
    Step 0: Tách dữ liệu dựa trên tính chất 'Cơ sở giá'.
    - Nhóm 1: Lấy theo báo giá, Giá thấp nhất...
    - Nhóm 2: Các loại còn lại (HĐ, v.v.)
    """
    print("📊 [Step 0] Đang phân loại vật tư theo nguồn gốc giá...")
    
    # Điều kiện lọc: Cột 'Price_base' chứa từ khóa liên quan báo giá
    keywords = ['báo giá', 'thấp nhất', 'bg']
    pattern = '|'.join(keywords)
    
    # Nhóm báo giá
    mask_bg = df_input['Price_base'].str.contains(pattern, case=False, na=False)
    df_baogia = df_input[mask_bg].copy()
    
    # Nhóm còn lại (HĐ, Khác...)
    df_others = df_input[~mask_bg].copy()
    
    return df_baogia, df_others
def classify_warning(score, diff_pct):
    """
    Tiêu chí đánh giá theo yêu cầu của Hiếu:
    - Chỉ đánh giá khi Score = 100.
    - Phân mức dựa trên % chênh lệch.
    """
    if score < 100:
        return "" # Không đánh giá nếu không khớp tuyệt đối
    
    x = diff_pct
    if 10 < x <= 20:
        return "⚠️ Cảnh báo Mức 1 (10-20%)"
    elif 20 < x <= 50:
        return "🚨 Cảnh báo Mức 2 (20-50%)"
    elif x > 50:
        return "🔥 Cảnh báo Mức 3 (>50%)"
    elif x > 10:
        return "🔎 Cần xem xét"
    
    return "✅ OK"

def fuzzy_match_history(df_source, df_history, suffix_name):
    """
    So khớp mờ và thêm cột Đánh giá tự động.
    """
    print(f"🕵️ Đang so khớp với {suffix_name}...")
    
    df_history['TVT_hist_clean'] = df_history['TVT'].apply(clean_text_vinh_tan)
    hist_list = df_history['TVT_hist_clean'].tolist()
    
    results = []
    for _, row in df_source.iterrows():
        match = process.extractOne(row['TVT_clean'], hist_list, scorer=fuzz.token_sort_ratio)
        
        if match and match[1] >= 75:
            idx = match[2]
            dg_hist = df_history.iloc[idx]['DG']
            score = round(match[1], 1)
            diff_pct = round(((row['DG'] - dg_hist) / dg_hist * 100) if dg_hist != 0 else 0, 2)
            
            res_row = {
                'MG': row['MG'],
                f'TVT_{suffix_name}': df_history.iloc[idx]['TVT'],
                f'DG_{suffix_name}': dg_hist,
                f'Score_{suffix_name}': score,
                f'Diff_Pct_{suffix_name}': diff_pct,
                f'Danh_Gia_{suffix_name}': classify_warning(score, diff_pct) # Cột kết luận
            }
            
            # Thêm cột phụ tùy theo kho
            if 'Ma_ERP_TTS1' in df_history.columns:
                res_row[f'Ma_ERP_{suffix_name}'] = df_history.iloc[idx]['Ma_ERP_TTS1']
            if 'history' in df_history.columns:
                res_row[f'History_{suffix_name}'] = df_history.iloc[idx]['history']
                res_row[f'Over1year_{suffix_name}'] = df_history.iloc[idx]['over1year']
                
            results.append(res_row)
        else:
            results.append({'MG': row['MG'], f'TVT_{suffix_name}': "KHÔNG KHỚP", f'Danh_Gia_{suffix_name}': ""})
            
    return pd.merge(df_source, pd.DataFrame(results), on='MG', how='left')