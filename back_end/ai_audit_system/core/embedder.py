import torch
import numpy as np
from sentence_transformers import SentenceTransformer

class DataEmbedder:
    def __init__(self):
        # Đường dẫn tới folder BGE Hiếu đã chụp ảnh
        model_path = r"D:\TaskApp_pro\search_item\back_end\AI_models\BGE"
        
        print(f"🚀 Đang nạp BGE-M3 bằng PyTorch từ: {model_path}")
        
        # Kiểm tra máy có Card đồ họa NVIDIA không, không có thì dùng CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Nạp model
        self.model = SentenceTransformer(model_path, device=self.device)
        print(f"✅ Đã nạp xong BGE-M3 trên {self.device.upper()}")

    def embed_documents(self, texts):
        # Giảm batch_size xuống 16 để tránh tràn RAM máy văn phòng
        # show_progress_bar=True để Hiếu theo dõi được nó đang chạy đến đâu
        embeddings = self.model.encode(
            texts, 
            batch_size=16, 
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Giải phóng bộ nhớ đệm ngay lập tức sau khi xong
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return embeddings

    def embed_query(self, query):
        return self.model.encode([query])[0]

# Test nhanh nếu chạy trực tiếp file này
if __name__ == "__main__":
    embedder = DataEmbedder()
    test_vec = embedder.embed_query("Máy cắt chân không VCB")
    print(f"Véc-tơ mẫu (5 chiều đầu): {test_vec[:5]}")
    print(f"Kích thước vector: {len(test_vec)}")