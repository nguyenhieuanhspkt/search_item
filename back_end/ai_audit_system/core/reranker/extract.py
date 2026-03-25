import re

class FeatureExtractor:
    def __init__(self, brands_list, materials_list):
        self.brands = set(brands_list)
        self.materials = set(materials_list)
        self.spec_units = r'(phi|dn|pn|sch|inch|kw|v|amp|mm|deg|bar|kg)'

    def extract_model(self, text):
        # Ưu tiên các chuỗi Alphanumeric (chữ + số) dài > 2 ký tự
        models = re.findall(r'\b(?=[a-z]*[0-9])(?=[0-9]*[a-z])[a-z0-9-]{3,}\b', text.lower())
        # Hoặc các mã hiệu đặc thù chỉ có số dài (part number)
        part_numbers = re.findall(r'\b\d{5,}[a-z0-9-]*\b', text.lower())
        return set(models + part_numbers)

    def get_features(self, text):
        text = text.lower()
        models = self.extract_model(text)
        
        # Xóa model khỏi text để tránh trùng lặp khi tìm brand/specs
        clean_text = text
        for m in models: clean_text = clean_text.replace(m, "")
        
        words = re.findall(r'\b\w+\b', clean_text)
        features = {
            "MODEL": [m.upper() for m in models],
            "BRAND": [],
            "SPECS": [],
            "NAME": []
        }

        for word in words:
            if word in self.brands:
                features["BRAND"].append(word.upper())
            elif word in self.materials or re.match(self.spec_units, word):
                features["SPECS"].append(word.upper())
            elif len(word) > 2:
                features["NAME"].append(word)
                
        return features