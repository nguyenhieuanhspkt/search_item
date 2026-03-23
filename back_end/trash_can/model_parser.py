import re
from typing import Dict, List, Set
from .helpers import extract_all_numbers, has_token # Tận dụng helper của Hiếu

class ModelParser:
    def __init__(self):
        # Các nhãn hiệu & mác thép phổ biến tại Vĩnh Tân 4
        self.brands = {"SIEMENS", "ABB", "SCHNEIDER", "OMRON", "EMERSON", "DANFOSS", "SKF"}
        self.materials = {"SA240", "SUS304", "SUS316", "310S", "A105", "Q235"}

    def parse(self, text: str) -> Dict:
        if not text: return {}
        text_up = text.upper()
        
        # 1. Tận dụng extract_all_numbers của Hiếu để lấy các thông số kỹ thuật
        all_numbers = extract_all_numbers(text_up)
        
        # 2. Trích xuất mã hiệu (Model/Part Number) 
        # Cải tiến Regex để bắt các mã phức tạp như 6AV6647-0AA11...
        # Quy tắc: Chuỗi có cả chữ và số, có dấu gạch ngang/chấm, dài ít nhất 4 ký tự
        model_pattern = r'\b(?=[A-Z]*\d)(?=[0-9]*[A-Z])[A-Z0-9\-\.\/]{4,}\b'
        models = re.findall(model_pattern, text_up)
        
        # 3. Trích xuất hãng và vật liệu (dùng has_token của Hiếu cho chính xác)
        found_brands = [b for b in self.brands if has_token(b, text_up)]
        found_mats = [m for m in self.materials if has_token(m, text_up)]

        return {
            "models": list(set(models)),
            "numbers": all_numbers,
            "brands": found_brands,
            "materials": found_mats
        }