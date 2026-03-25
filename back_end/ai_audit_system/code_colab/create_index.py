import os
import pandas as pd
import numpy as np
import torch
import faiss
import json
import re
import yaml
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
from google.colab import files

# ============================================================
# 1. CẤU HÌNH NORMALIZER V6.0 (GIỮ NGUYÊN LOGIC ƯU TIÊN MÃ HIỆU)
# ============================================================
class Normalizer:
    def __init__(self, config_path="config"):
        self.config_path = config_path
        self.synonyms = self._load_yaml("synonyms.yaml")
        self.materials = self._load_yaml("materials.yaml")
        self.units = self._load_yaml("units.yaml")
        self.domains = self._load_yaml("domains.yaml")

    def _load_yaml(self, filename):
        path = os.path.join(self.config_path, filename)
        if not os.path.exists(path): return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

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
        # Ưu tiên mã hiệu lặp lại 2 lần ở đầu
        return re.sub(r"\s+", " ", f"{code_str} {code_str} {cleaned}").strip()

# ============================================================
# 2. KHỞI TẠO MODEL BGE-M3 QUA PYTORCH
# ============================================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "BAAI/bge-m3"

print(f"📦 Đang tải model {model_name} lên {device}...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)
model.eval()

def get_embeddings(texts, batch_size=32):
    all_embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="🤖 Đang tạo Vector"):
        batch_texts = texts[i:i+batch_size]
        encoded_input = tokenizer(batch_texts, padding=True, truncation=True, return_tensors='pt', max_length=512).to(device)
        with torch.no_grad():
            model_output = model(**encoded_input)
            # Lấy [CLS] token làm đại diện cho vector (chuẩn của BGE)
            sentence_embeddings = model_output[0][:, 0]
            # Normalize vector về độ dài 1 (để tính Cosine Similarity)
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
            all_embeddings.append(sentence_embeddings.cpu().numpy())
    return np.vstack(all_embeddings)

# ============================================================
# 3. THỰC THI XỬ LÝ DỮ LIỆU
# ============================================================
ERP_FILE = "Data_For_Meili.xlsx"
CONFIG_FOLDER = "config"

print("📖 Đọc dữ liệu ERP...")
df = pd.read_excel(ERP_FILE, engine="openpyxl")
norm = Normalizer(CONFIG_FOLDER)

print("🛠️ Chuẩn hóa văn bản...")
texts_to_embed = [norm.normalize(f"{str(r['Tên vật tư (NXT)'])} {str(r['Thông số kỹ thuật'])}") for _, r in df.iterrows()]

print("🚀 Bắt đầu tạo Embedding với PyTorch...")
embeddings = get_embeddings(texts_to_embed)

print("🏗️ Xây dựng FAISS Index...")
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension) # Inner Product + Normalized L2 = Cosine Similarity
index.add(embeddings.astype('float32'))

print("💾 Lưu file kết quả...")
faiss.write_index(index, "faiss.index")

meta_columns = ['Mã vật tư', 'Tên vật tư (NXT)', 'Đơn vị tính', 'Thông số kỹ thuật']
metadata = df[meta_columns].fillna("").to_dict(orient='records')
with open("faiss_meta.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=4)

print("✅ Hoàn thành!")
files.download("faiss.index")
files.download("faiss_meta.json")




# Quy trình tiếp theo: Hiếu chỉ cần lưu file này lại, sau đó mở main.py lên và tận hưởng kết quả "AI Audit" thế hệ mới. Những dòng khó như "Khớp giãn nở LHB6.6T" bây giờ sẽ được AI ưu tiên xử lý đúng model trước khi nhìn đến chữ "Khớp".

# Hiếu đã sẵn sàng chạy thử main.py với bộ não mới chưa?
