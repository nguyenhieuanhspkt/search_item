# 1. Chọn hệ điều hành nền (có sẵn Python 3.10)
FROM python:3.10-slim

# 2. Cài đặt các công cụ hệ thống cần thiết (cho FAISS hoặc các thư viện C++)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Khai báo thư mục làm việc bên trong Docker
WORKDIR /app

# 4. Copy file danh sách thư viện vào trước để cài đặt
COPY requirements.txt .

# 5. Cài đặt các thư viện (PyTorch, FastAPI, BGE-M3...)
# Lưu ý: pip sẽ cài bản CPU nếu Hiếu không cấu hình CUDA đặc biệt
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy toàn bộ code từ máy Hiếu vào trong Docker
COPY . .

# 7. Mở cổng 8000 để máy ngoài có thể gọi API
EXPOSE 8000

# 8. Câu lệnh để khởi động Backend khi Docker bật lên
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]