import pandas as pd
import re

# --- CÁC HÀM CƠ BẢN (STEP 1 - 3) ---
def step_1_to_3_load_data(file_1_path, file_2_path, file_3_path):
    """Nạp 5 nguồn dữ liệu từ 3 file khác nhau"""
    print(f"📖 Đang nạp dữ liệu tổng hợp từ 3 File...")
    
    # File 1: Dự toán, Cơ sở giá, ERP
    df1 = pd.read_excel(file_1_path, sheet_name="PL1.5 DT VẬT TƯ TM")
    df2 = pd.read_excel(file_1_path, sheet_name="Cơ sở giá")
    df4 = pd.read_excel(file_1_path, sheet_name="ERP")
    
    # File 2: Kho S1
    df3 = pd.read_excel(file_2_path, sheet_name="PL1.5 DT VẬT TƯ TM")
    
    # File 3: Huyền (df5)
    print(f"📖 Đang nạp df5 từ dòng 3 (Header=2)...")
    df5 = pd.read_excel(file_3_path,sheet_name="Dự toán",header=2) # Hiếu bổ sung sheet_name nếu cần
    print(f"📊 df5 nạp thành công: {len(df5.columns)} cột.")
    # --- BƯỚC LỌC DÒNG THEO CỘT B (STT) ---
    # Lấy cột B (Index 1). Nếu ô đó trống (NaN) hoặc là chuỗi rỗng thì loại bỏ.
    # .notna() loại bỏ NaN, .astype(str).str.strip() != "" loại bỏ các ô chỉ có dấu cách
    df5 = df5[df5.iloc[:, 1].notna()] 
    df5 = df5[df5.iloc[:, 1].astype(str).str.strip() != ""]
    
    print(f"🧹 Sau khi lọc theo cột B, df5 còn lại: {len(df5)} dòng vật tư.")
    # --- CHUẨN HÓA DF3 & DF4 (Giữ nguyên logic cũ) ---
    df3.rename(columns={df3.columns[3]: 'TVT', df3.columns[12]: 'DG', df3.columns[18]: 'Ma_ERP_TTS1'}, inplace=True)
    
    mapping_df4 = {df4.columns[1]: 'TVT_Goc', df4.columns[2]: 'DG', df4.columns[3]: 'DVT', 
                   df4.columns[9]: 'history', df4.columns[10]: 'over1year', df4.columns[11]: 'TSKT'}
    df4.rename(columns=mapping_df4, inplace=True)
    df4['TVT'] = df4['TVT_Goc'].astype(str) + " " + df4['TSKT'].fillna("").astype(str)

    # --- CHUẨN HÓA DF5 (File 3) ---
    # Tọa độ: L(11), M(12), C(2), O(14), P(15), Q(16), T(19), U(20)
    # Nhà thầu báo giá: W(22) đến AB(27) -> Ta lấy giá thấp nhất hoặc trung bình tùy Hiếu, 
    # ở đây mình lấy cột W làm giá đại diện (DG) để so sánh.
    # RENAME THEO THỨ TỰ INDEX TĂNG DẦN (Từ trái qua phải)
    # --- CHUẨN HÓA DF5 (FILE 3) ---
    # Header dòng 3 (header=2)
    mapping_df5 = {
        df5.columns[1]:  'STT_df5',    # B (Index 1) - STT
        df5.columns[2]:  'Ma_SCL',     # C (Index 2) - MG
        df5.columns[11]: 'TVT_Goc',    # L (Index 11)
        df5.columns[12]: 'TSKT',       # M (Index 12)
        df5.columns[14]: 'DVT',        # O (Index 14)
        df5.columns[15]: 'KL_df5',     # P (Index 15)
        df5.columns[18]: 'DG',         # S (Index 18) - Đơn giá
        df5.columns[19]: 'TT_df5',     # T (Index 19) - Thành tiền
        df5.columns[20]: 'Ghi_chu'     # U (Index 20)
    }
    
    # Thực hiện đổi tên
    df5.rename(columns=mapping_df5, inplace=True)
    
    # Xử lý gộp Tên + Thông số kỹ thuật cho df5
    df5['TVT'] = df5['TVT_Goc'].astype(str).str.strip() + " " + df5['TSKT'].fillna("").astype(str).str.strip()
    df5['TVT'] = df5['TVT'].str.replace(r'\s+', ' ', regex=True).str.strip()
    

    return df1, df2, df3, df4, df5

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

def fuzzy_match_history(df_left, df_history, suffix_name):
    """
    So khớp mờ và chỉ giữ lại các cột cốt lõi từ kho lịch sử.
    """
    print(f"🕵️ Đang so khớp mờ với {suffix_name}...")
    
    # Chuẩn hóa cột TVT của kho lịch sử để so sánh
    df_history['TVT_hist_clean'] = df_history['TVT'].apply(clean_text_vinh_tan)
    hist_list = df_history['TVT_hist_clean'].tolist()
    
    results = []
    
    # SỬA LỖI: Duyệt qua df_left (biến đầu vào) thay vì df_source
    for _, row in df_left.iterrows():
        # Kiểm tra xem dòng hiện tại có TVT_clean không (nếu chưa có thì tạo)
        target_text = row['TVT_clean'] if 'TVT_clean' in row else clean_text_vinh_tan(row['TVT'])
        
        # Thực hiện ExtractOne
        match = process.extractOne(target_text, hist_list, scorer=fuzz.token_sort_ratio)
        
        if match and match[1] >= 90:
            idx = match[2]
            dg_hist = df_history.iloc[idx]['DG']
            score = round(match[1], 1)
            
            # Tính toán chênh lệch % ngay tại đây
            dg_current = row['DG']
            diff_pct = round(((dg_current - dg_hist) / dg_hist * 100) if dg_hist != 0 else 0, 2)
            
            res_row = {
                f'TVT_{suffix_name}': df_history.iloc[idx]['TVT'],
                f'DG_{suffix_name}': dg_hist,
                f'Diff_{suffix_name}_Pct': diff_pct, # Cột so sánh đơn giá
                f'Score_{suffix_name}': score,
                f'Danh_Gia_{suffix_name}': classify_warning(score, diff_pct)
            }
            
            # Giữ lại các cột đặc thù nếu có
            if 'Ma_ERP_TTS1' in df_history.columns:
                res_row[f'Ma_ERP_{suffix_name}'] = df_history.iloc[idx]['Ma_ERP_TTS1']
            if 'over1year' in df_history.columns:
                res_row[f'Over1year_{suffix_name}'] = df_history.iloc[idx]['over1year']
                
            results.append(res_row)
        else:
            # Nếu không khớp, trả về giá trị trống để bảng vẫn giữ nguyên số dòng
            results.append({
                f'TVT_{suffix_name}': "KHÔNG KHỚP", 
                f'DG_{suffix_name}': 0, 
                f'Diff_{suffix_name}_Pct': 0,
                f'Danh_Gia_{suffix_name}': ""
            })

    # Tạo DataFrame kết quả từ list results
    res_df = pd.DataFrame(results)
    
    # Ghép bảng kết quả (Right side) vào bảng gốc (Left side)
    # Dùng concat theo trục ngang (axis=1) để đảm bảo số dòng khớp tuyệt đối
    df_final = pd.concat([df_left.reset_index(drop=True), res_df], axis=1)
    
    return df_final
    
def compare_df5_with_others(df5_raw, df1_unique, df3_raw, df4_raw):
    """
    Hàm đối chiếu df5 (Sheet 4) - Rút gọn cột tối đa.
    - Trái (df5): STT, TVT, TSKT, DVT, DG, TT.
    - Phải (df1): TVT, DG (Khớp theo MG).
    - Phải (S1, ERP): TVT, DG (Khớp mờ).
    """
    print("🧹 Đang thực hiện đối chiếu và tinh giản cột cho df5...")

    # --- BƯỚC 1: CHUẨN BỊ BẢNG BÊN TRÁI (df5) ---
    # Chỉ giữ lại các cột Hiếu yêu cầu
    cols_left = ['STT_df5', 'Ma_SCL', 'TVT', 'TSKT', 'DVT', 'DG', 'TT_df5']
    df_result = df5_raw[cols_left].copy()

    # --- BƯỚC 2: KHỚP VỚI DF1 (DỰ TOÁN) QUA MÃ GIÁ (MG) ---
    # Chỉ lấy TVT và DG của df1 để đưa vào bảng bên phải
    df1_right = df1_unique[['MG', 'TVT', 'DG']].rename(columns={
        'TVT': 'TVT_df1', 
        'DG': 'DG_df1'
    })

    # Dùng merge như cũ để đảm bảo chính xác theo Mã SCL = MG
    df_result = pd.merge(df_result, df1_right, left_on='Ma_SCL', right_on='MG', how='left')

    # --- BƯỚC 3: ÉP KIỂU SỐ VÀ TÍNH % LỆCH DF5 VS DF1 ---
    df_result['DG'] = pd.to_numeric(df_result['DG'], errors='coerce').fillna(0)
    df_result['DG_df1'] = pd.to_numeric(df_result['DG_df1'], errors='coerce').fillna(0)
    
    df_result['Diff_df5_vs_df1_Pct'] = 0.0
    mask = df_result['DG_df1'] != 0
    df_result.loc[mask, 'Diff_df5_vs_df1_Pct'] = round(
        ((df_result.loc[mask, 'DG'] - df_result.loc[mask, 'DG_df1']) / df_result.loc[mask, 'DG_df1'] * 100), 2
    )

    # --- BƯỚC 4: KÉO THÊM GIÁ S1 VÀ ERP (SO KHỚP MỜ) ---
    # Ở đây mình gọi hàm fuzzy_match để điền thêm cột bên phải
    from processors import fuzzy_match_history
    
    # Chỉ lấy TVT và DG từ S1/ERP để bảng không bị phình to
    df_result = fuzzy_match_history(df_result, df3_raw, "S1")
    df_result = fuzzy_match_history(df_result, df4_raw, "ERP")

    # --- BƯỚC 5: LỌC LẠI CÁC CỘT CUỐI CÙNG ---
    final_cols = [
        'STT_df5', 'Ma_SCL', 'TVT', 'TSKT', 'DVT', 'DG', 'TT_df5', # Bên trái
        'TVT_df1', 'DG_df1', 'Diff_df5_vs_df1_Pct',               # Bên phải (df1)
        'DG_S1', 'Diff_S1_Pct',                                   # Bên phải (S1)
        'DG_ERP', 'Diff_ERP_Pct'                                  # Bên phải (ERP)
    ]
    
    # Chỉ lấy những cột tồn tại
    df_result = df_result[[c for c in final_cols if c in df_result.columns]]

    print(f"✅ Đã gọt cột xong. Tổng cộng {len(df_result)} dòng.")
    return df_result