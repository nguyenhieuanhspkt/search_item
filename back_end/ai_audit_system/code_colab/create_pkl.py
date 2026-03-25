import pandas as pd
import pickle
import json
from google.colab import files

# 1. Khai báo file và cột cần lấy
ERP_FILE = "Data_For_Meili.xlsx" # Tên file ERP Hiếu đã upload lên Colab
# Các cột quan trọng để hiển thị kết quả thẩm định
META_COLUMNS = ['Mã vật tư', 'Tên vật tư (NXT)', 'Đơn vị tính', 'Thông số kỹ thuật']

print("📖 Đang đọc file Excel...")
df = pd.read_excel(ERP_FILE, engine="openpyxl")

# 2. Xử lý dữ liệu (Xóa bỏ các giá trị trống để tránh lỗi)
print("🛠️ Đang đóng gói Metadata...")
metadata = df[META_COLUMNS].fillna("").to_dict(orient='records')

# 3. Lưu thành file .pkl (Pickle - Định dạng nhị phân siêu nhanh)
PKL_FILENAME = "faiss_meta.pkl"
with open(PKL_FILENAME, "wb") as f:
    pickle.dump(metadata, f)

# 4. Lưu thêm bản .json (Để Hiếu có thể mở xem bằng Notepad nếu cần)
JSON_FILENAME = "faiss_meta.json"
with open(JSON_FILENAME, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=4)

print(f"✅ Đã tạo xong: {len(metadata)} dòng dữ liệu.")
print("🚀 Đang chuẩn bị tải về...")

# 5. Tải file về máy tính của Hiếu
files.download(PKL_FILENAME)
files.download(JSON_FILENAME)