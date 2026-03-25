# 1. Cài đặt các thư viện (Bản dành riêng cho CPU)
!pip install faiss-cpu pandas openpyxl pyyaml transformers torch tqdm

import os
import pandas as pd
import numpy as np
import torch
import faiss
import json
import re
import yaml
import pickle
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
from google.colab import files

# ============================================================
# 1. CẤU HÌNH NORMALIZER (GIỮ NGUYÊN LOGIC MODEL/THÔNG SỐ)
# ============================================================
class Normalizer:
    def __init__(self, config_path="config"):
        if not os.path.exists(config_path): os.makedirs(config_path)
        
    def clean_basic(self, text: str) -> str:
        if not isinstance(text, str): return ""
        text = text.strip().lower()
        text = re.sub(r"[^\w\s\/\.\-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def extract_technical_codes(self, text: str):
        codes = re.findall(r"\b[a-z0-9]*[0-9][a-z0-9]*[-._/][a-z0-9]*[0-9][a-z0-9]*\b|\b[a-z]{1,2}[0-9]{3,}\b|\b[0-9]{6,}\b", text)
        dn_pn = re.findall(r"\b(?:dn|pn|dia|od|id)\s*\d+\b", text)
        return list(set(codes + dn_pn))

    def normalize(self, text: str) -> str:
        cleaned = self.clean_basic(text)
        tech_codes = self.extract_technical_codes(cleaned)
        code_str = " ".join(tech_codes)
        return re.sub(r"\s+", " ", f"{code_str} {code_str} {cleaned}").strip()

# ============================================================
# 2. KHỞI TẠO MODEL BGE-M3 (CHẠY THUẦN CPU)
# ============================================================
# Cưỡng ép dùng CPU kể cả khi Colab có GPU
device = torch.device("cpu")
model_name = "BAAI/bge-m3"

print(f"📦 Đang tải model {model_name} lên CPU...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)
model.eval()

def get_embeddings(texts, batch_size=8): # Batch size nhỏ để CPU không bị treo
    all_embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="🤖 AI đang tạo Vector"):
        batch_texts = texts[i:i+batch_size]
        encoded_input = tokenizer(batch_texts, padding=True, truncation=True, return_tensors='pt', max_length=512).to(device)
        with torch.no_grad():
            model_output = model(**encoded_input)
            # Lấy [CLS] token và Normalize
            sentence_embeddings = model_output[0][:, 0]
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
            all_embeddings.append(sentence_embeddings.numpy()) # CPU dùng trực tiếp numpy
    return np.vstack(all_embeddings)

# ============================================================
# 3. XỬ LÝ DỮ LIỆU & XUẤT FILE (FULL CỘT GIÁ/DIỄN GIẢI)
# ============================================================
print("📂 Vui lòng chọn file 'Data_For_Meili.xlsx' (20,015 dòng):")
uploaded = files.upload()
ERP_FILE = list(uploaded.keys())[0]

print("📖 Đang đọc dữ liệu...")
df = pd.read_excel(ERP_FILE, engine="openpyxl")
df = df.fillna("") # Xử lý ô trống

norm = Normalizer()

# Tạo danh sách văn bản để AI "học"
print("🛠️ Chuẩn hóa dữ liệu...")
texts_to_embed = [norm.normalize(f"{str(r['Tên vật tư (NXT)'])} {str(r['Thông số kỹ thuật'])}") for _, r in df.iterrows()]

# Tạo Vector
embeddings = get_embeddings(texts_to_embed)

# Xây dựng Index FAISS cho CPU
print("🏗️ Đang xây dựng bộ nhớ FAISS Index...")
dimension = embeddings.shape[1]
# IndexFlatIP là chuẩn nhất cho Cosine Similarity trên CPU
index = faiss.IndexFlatIP(dimension) 
index.add(embeddings.astype('float32'))

# Đóng gói Full Metadata (Thêm Giá, Diễn giải, Hợp đồng...)
print("💾 Đóng gói Metadata đầy đủ...")
meta_columns = [
    'Mã vật tư', 'Tên vật tư (NXT)', 'Đơn Giá Nhập', 'Đơn vị tính', 
    'Số Hợp Đồng/QĐ', 'Năm', 'Kho', 'Diễn Giải', 'Thông số kỹ thuật'
]
existing_cols = [c for c in meta_columns if c in df.columns]
metadata = df[existing_cols].to_dict(orient='records')

# Lưu file
faiss.write_index(index, "faiss.index")
with open("faiss_meta.pkl", "wb") as f:
    pickle.dump(metadata, f)
with open("faiss_meta.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=4)

print("\n✅ HOÀN THÀNH! Hiếu tải 2 file .index và .pkl về máy nhé.")
files.download("faiss.index")
files.download("faiss_meta.pkl")