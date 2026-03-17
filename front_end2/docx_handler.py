from docx import Document
import pandas as pd

def extract_table_from_docx(file):
    """
    Trích xuất dữ liệu từ tất cả các bảng trong file Word.
    Cấu trúc mong đợi: Cột 0: STT, Cột 1: Tên, Cột 2: Thông số, Cột 3: ĐVT
    """
    try:
        # Load file từ bộ nhớ (Streamlit UploadedFile)
        doc = Document(file)
        all_data = []

        for table_index, table in enumerate(doc.tables):
            # Duyệt từng hàng, bỏ qua hàng đầu tiên (thường là tiêu đề)
            for row_index, row in enumerate(table.rows[1:]):
                cells = row.cells
                
                # Kiểm tra số lượng cột tối thiểu để tránh lỗi Index
                if len(cells) >= 4:
                    # Làm sạch dữ liệu (loại bỏ khoảng trắng thừa, xuống dòng)
                    stt = cells[0].text.strip()
                    ten = cells[1].text.strip()
                    ts = cells[2].text.strip()
                    dvt = cells[3].text.strip()

                    # Chỉ thêm vào danh sách nếu dòng đó thực sự có tên vật tư
                    # Tránh lấy các dòng trống hoặc dòng ghi chú ở cuối bảng
                    if ten: 
                        all_data.append({
                            "stt": stt,
                            "ten": ten,
                            "ts": ts,
                            "dvt_word": dvt,
                            "source_table": table_index + 1 # Để biết dữ liệu từ bảng nào
                        })
                else:
                    # Ghi log nhẹ nếu phát hiện dòng không đủ cấu trúc (tùy chọn)
                    continue
        
        return all_data

    except Exception as e:
        # Trong môi trường thực tế, bạn nên dùng logging thay vì print
        print(f"❌ Lỗi nghiêm trọng khi đọc file Word: {str(e)}")
        return []

def get_preview_df(data):
    """Hàm hỗ trợ chuyển đổi nhanh sang DataFrame để Streamlit hiển thị"""
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)