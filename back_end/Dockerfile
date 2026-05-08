# 1. Sử dụng Python phiên bản nhẹ (slim)
FROM python:3.9-slim

# 2. Đặt thư mục làm việc trong Docker
WORKDIR /app

# 3. Copy file thư viện vào và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy toàn bộ code vào Docker
COPY . .

# 5. Mở cổng mà FastAPI/Uvicorn thường dùng (thường là 8000)
EXPOSE 8000

# 6. Lệnh khởi chạy uvicorn
# Giả sử file chính của bạn là main.py và biến app nằm trong đó
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]