from docx import Document
import pandas as pd

def extract_table_from_docx(file):
    try:
        doc = Document(file)
        data = []
        for table in doc.tables:
            for row in table.rows[1:]: # Bỏ qua header
                cells = row.cells
                if len(cells) >= 4:
                    data.append({
                        "stt": cells[0].text.strip(),
                        "ten": cells[1].text.strip(),
                        "ts": cells[2].text.strip(),
                        "dvt_word": cells[3].text.strip()
                    })
        return data
    except Exception as e:
        print(f"Lỗi đọc file Word: {e}")
        return []