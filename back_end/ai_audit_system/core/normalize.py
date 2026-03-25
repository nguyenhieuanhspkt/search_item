# ai_audit_system\core\normalize.py
import re
import yaml
import os

class Normalizer:
    PROT_TAG_START = "__CODE_"
    PROT_TAG_END = "__"

    def __init__(self, config_path="config"):
        self.config_path = config_path
        self.synonyms = self._load_yaml("synonyms.yaml")
        self.materials = self._load_yaml("materials.yaml")
        self.units = self._load_yaml("units.yaml")
        self.domains = self._load_yaml("domains.yaml")

        if "groups" in self.synonyms:
            for g in self.synonyms["groups"]:
                g["terms"] = sorted(g["terms"], key=len, reverse=True)

    def _load_yaml(self, filename):
        path = os.path.join(self.config_path, filename)
        if not os.path.exists(path): return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def clean_basic(self, text: str) -> str:
        if not isinstance(text, str): return ""
        text = text.strip().lower()
        # Giữ lại các ký tự quan trọng cho Model/Mã hiệu
        text = re.sub(r"[^\w\s\/\.\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_technical_codes(self, text: str):
        """
        Trích xuất các 'linh hồn' của vật tư: Model, Part Number, Thông số DN/PN
        """
        # 1. Tìm Part Number/Model (Chuỗi có cả chữ và số, hoặc dãy số dài)
        # Ví dụ: LHB6.6T, FW-202FL, 1617907483
        codes = re.findall(r"\b[a-z0-9]*[0-9][a-z0-9]*[-._/][a-z0-9]*[0-9][a-z0-9]*\b|\b[a-z]{1,2}[0-9]{3,}\b|\b[0-9]{6,}\b", text)
        
        # 2. Tìm thông số kích thước tiêu chuẩn
        dn_pn = re.findall(r"\b(?:dn|pn|dia|od|id)\s*\d+\b", text)
        dims = re.findall(r"\d+\s*x\s*\d+(?:\s*x\s*\d+)?", text)
        
        return list(set(codes + dn_pn + dims))

    def detect_domain(self, text):
        t = text.lower()
        if not self.domains or "domain_rules" not in self.domains: return "general"
        for domain, conf in self.domains["domain_rules"].items():
            for kw in conf["keywords"]:
                if kw in t: return domain
        return "general"

    def apply_hybrid_mapping(self, text: str) -> str:
        """Chỉ thực hiện mapping trên phần văn bản ĐÃ TÁCH MÃ HIỆU"""
        domain = self.detect_domain(text)
        
        # Protect & Map Synonyms
        out = text
        if "groups" in self.synonyms:
            for group in self.synonyms["groups"]:
                if "domain" in group and domain not in (group["domain"], "general"): continue
                # Sử dụng tag bảo vệ để không bị các quy tắc sau đè lên
                pattern = rf"\b({'|'.join([re.escape(t) for t in group['terms']])})\b"
                out = re.sub(pattern, f" {group['canonical']} ", out)

        # Map Materials & Units
        # (Giữ nguyên logic cũ của Hiếu nhưng chạy trên text đã lọc mã)
        return out

    def normalize(self, text: str) -> str:
        # BƯỚC 1: Làm sạch và tách Mã hiệu
        cleaned = self.clean_basic(text)
        tech_codes = self.extract_technical_codes(cleaned)
        
        # BƯỚC 2: Tạo bản text tạm thời đã loại bỏ mã hiệu để Mapping không làm 'loãng'
        temp_text = cleaned
        for code in tech_codes:
            # Thay thế chính xác cụm mã hiệu bằng khoảng trắng
            temp_text = re.sub(rf"\b{re.escape(code)}\b", " ", temp_text)
        
        # BƯỚC 3: Mapping ngôn ngữ (Chuyển Van bướm -> Butterfly Valve...)
        mapped_text = self.apply_hybrid_mapping(temp_text)
        
        # BƯỚC 4: TÁI CẤU TRÚC CHUỖI VỚI TRỌNG SỐ MÃ HIỆU
        # Đưa mã hiệu lên đầu và lặp lại 2 lần để AI tập trung vào nó nhất
        code_str = " ".join(tech_codes)
        
        # Kết cấu: [MÃ HIỆU] [MÃ HIỆU] [VĂN BẢN MAPPING]
        # Điều này giúp BGE-M3 hiểu rằng nếu khớp được code_str thì Score sẽ cực thấp (tốt)
        final_output = f"{code_str} {code_str} {mapped_text}"
        
        # Clean khoảng trắng thừa
        final_output = re.sub(r"\s+", " ", final_output).strip()
        
        # Lọc trùng lặp từ liên tiếp (logic cũ của Hiếu)
        words = final_output.split()
        res = []
        for w in words:
            if not res or w != res[-1]: res.append(w)
            
        return " ".join(res)