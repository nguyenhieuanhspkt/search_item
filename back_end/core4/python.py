

from fastembed import TextEmbedding
import pandas as pd

# 1. Khởi tạo model (Bản này chạy CPU cực nhanh)
# Nó sẽ tự tải bản bge-m3 đã được tối ưu
model = TextEmbedding(model_name="BAAI/bge-m3")

# 2. Giả sử Hiếu có list 20k dòng ERP
documents = ["Vòng bi cầu 6205-2RS1", "Máy nén khí trục vít", "Van một chiều DN150"] * 7000 

print("⚡ Đang số hóa bằng CPU (Công nghệ FastEmbed)...")
# Hàm này chạy đa luồng trên CPU, tốc độ cực ấn tượng
embeddings = list(model.embed(documents)) 

print(f"✅ Đã xử lý xong {len(embeddings)} dòng mà không cần GPU!")