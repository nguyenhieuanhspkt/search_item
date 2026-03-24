import re
import yaml
import os

class Normalizer:
    PROT_TAG_START = "__PROT_START__"
    PROT_TAG_END = "__PROT_END__"

    def __init__(self, config_path="config"):
        self.config_path = config_path
        self.synonyms = self._load_yaml("synonyms.yaml") # Load toàn bộ dict
        self.materials = self._load_yaml("materials.yaml")
        self.units = self._load_yaml("units.yaml")
        self.domains = self._load_yaml("domains.yaml") # Đã thêm line này

        # Sắp xếp terms theo độ dài giảm dần
        if "groups" in self.synonyms:
            for g in self.synonyms["groups"]:
                g["terms"] = sorted(g["terms"], key=len, reverse=True)

    def _load_yaml(self, filename):
        path = os.path.join(self.config_path, filename)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # Đã đổi tên từ clean -> clean_basic để khớp với hàm normalize
    def clean_basic(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.strip().lower()
        text = re.sub(r"[^\w\s\/\.\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = text.replace(" - ", "-").replace(" / ", "/")
        return text

    def parse(self, text):
        cleaned = self.clean_basic(text)
        part_numbers = re.findall(
            r"[a-z0-9]{2,}(?:[-_/\.]?[a-z0-9]{2,}){1,}", cleaned, flags=re.IGNORECASE
        )
        dn = re.findall(r"\bdn\s*\d+\b", cleaned)
        pn = re.findall(r"\bpn\s*\d+\b", cleaned)
        dims = re.findall(r"\d+\s*x\s*\d+\s*x\s*\d+", cleaned)
        inch_sizes = re.findall(r"(\d+)\s*(?:inch|in|\")", cleaned)

        return {
            "original": text,
            "cleaned": cleaned,
            "part_numbers": part_numbers,
            "dn": dn,
            "pn": pn,
            "dimensions": dims,
            "inch": inch_sizes,
        }

    def detect_domain(self, text):
        t = text.lower()
        if not self.domains or "domain_rules" not in self.domains:
            return "general"
            
        for domain, conf in self.domains["domain_rules"].items():
            for kw in conf["keywords"]:
                if kw in t:
                    return domain
        return "general"

    def _protect(self, txt: str) -> str:
        return f"{self.PROT_TAG_START}{txt}{self.PROT_TAG_END}"

    def _unprotect(self, text: str) -> str:
        return text.replace(self.PROT_TAG_START, "").replace(self.PROT_TAG_END, "")

    def map_synonyms(self, text: str, domain=None) -> str:
        mapped = text
        if "groups" not in self.synonyms: return mapped

        for group in self.synonyms["groups"]:
            if "domain" in group and domain not in (group["domain"], "general"):
                continue
            canonical = self._protect(group["canonical"])
            for term in group["terms"]:
                pattern = rf"\b{re.escape(term)}\b"
                mapped = re.sub(pattern, canonical, mapped)

        # Xử lý từ đa nghĩa (BC, VC...)
        for amb in self.synonyms.get("ambiguous_terms", []):
            term = amb["term"]
            if re.search(rf"\b{term}\b", mapped):
                for m in amb["mappings"]:
                    if m["domain"] == domain:
                        mapped = re.sub(rf"\b{term}\b", self._protect(m["canonical"]), mapped)
                        break
        return mapped

    def map_materials(self, text):
        mapped = text
        if "materials" not in self.materials: return mapped
        for mat in self.materials["materials"]:
            canonical = self._protect(mat["canonical"])
            aliases = sorted(mat["aliases"], key=len, reverse=True)
            for alias in aliases:
                pattern = rf"\b{re.escape(alias)}\b"
                mapped = re.sub(pattern, canonical, mapped)
        return mapped

    def map_units(self, text):
        mapped = text
        if "units" not in self.units: return mapped
        for unit in self.units["units"]:
            canonical = self._protect(unit["canonical"])
            for t in unit["terms"]:
                pattern = rf"\b{re.escape(t)}\b"
                mapped = re.sub(pattern, canonical, mapped)
        return mapped

    # Đã thêm hàm này để điều phối toàn bộ việc mapping
    def apply_hybrid_mapping(self, cleaned_text: str) -> str:
        domain = self.detect_domain(cleaned_text)
        out = self.map_synonyms(cleaned_text, domain)
        out = self.map_materials(out)
        out = self.map_units(out)
        out = self._unprotect(out)
        return out

    def normalize(self, text: str) -> str:
        # 1. Làm sạch
        cleaned = self.clean_basic(text)
        
        # 2. Mapping (Gọi hàm vừa bổ sung ở trên)
        out = self.apply_hybrid_mapping(cleaned)
        
        # 3. Lọc trùng lặp liên tiếp
        words = out.split()
        if not words:
            return ""
        
        result_words = []
        for w in words:
            if not result_words or w != result_words[-1]:
                result_words.append(w)
        
        return " ".join(result_words)