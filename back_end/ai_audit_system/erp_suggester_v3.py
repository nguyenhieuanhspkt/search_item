import pandas as pd
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# 1. TEXT NORMALIZATION
# ============================================================
STOPWORDS = {
    "c", "m", "n", "t", "i", "k", "l", "p", "b", "v", "d",
    "sử", "dụng", "cho", "van", "bộ", "pos", "model",
    "item", "no", "nsx", "dw", "dw:", "theo", "vị", "trí"
}

def normalize(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\.\-\s/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    # remove stopwords
    tokens = [w for w in text.split() if w not in STOPWORDS]
    return " ".join(tokens).strip()


# ============================================================
# 2. BOOST FUNCTIONS
# ============================================================

def extract_part_numbers(text):
    # Long alphanumeric sequences or dashed codes
    return re.findall(r"[a-z0-9]{4,}[-a-z0-9]*", text.lower())


def part_number_boost(query, erp_text):
    q_pn = extract_part_numbers(query)
    score = 0
    for p in q_pn:
        if p in erp_text:
            score += 0.45
    return score


def size_boost(query, erp_text):
    dims = re.findall(r"\d+\s*x\s*\d+\s*x\s*\d+", query.lower())
    score = 0
    for d in dims:
        if d in erp_text:
            score += 0.30
    return score


def material_boost(query, erp_text):
    mats = ["sus304", "304", "316", "310s", "graphite", "ptfe", "a105", "ca40", "hardox", "ar500"]
    q = query.lower()
    e = erp_text.lower()
    score = 0
    for m in mats:
        if m in q and m in e:
            score += 0.20
    return score


# ============================================================
# 3. DOMAIN DETECTION & FILTERING
# ============================================================

def detect_domain(text):
    t = text.lower()

    if "ik-" in t or "soot" in t or "feed tube" in t or "diamond power" in t:
        return "sootblower"

    if "valve" in t or "tcv" in t or "globe" in t or "weir" in t:
        return "valve"

    if "atlas" in t or "copco" in t or "filter" in t:
        return "compressor"

    if "mechanical seal" in t or "seal" in t or "packing" in t:
        return "pump_seal"

    if "ar500" in t or "hardox" in t or "steel plate" in t or "thép tấm" in t:
        return "steel"

    return "general"


DOMAIN_KEYWORDS = {
    "sootblower": ["soot", "ik-", "feed tube", "poppet", "diamond power"],
    "valve": ["valve", "gasket", "seal", "tgv", "globe", "tcv", "weir"],
    "compressor": ["atlas", "copco", "filter", "element"],
    "pump_seal": ["seal", "packing", "mechanical"],
    "steel": ["hardox", "ar500", "plate", "steel"],
    "general": []
}


def domain_score(domain, erp_text):
    erp_lower = erp_text.lower()
    for kw in DOMAIN_KEYWORDS.get(domain, []):
        if kw in erp_lower:
            return 0.35
    return 0


# ============================================================
# 4. ERP ENGINE
# ============================================================

class ERPSuggester:

    def __init__(self, df_erp):
        df_erp["full_text"] = (
            df_erp["Tên vật tư (NXT)"].fillna("") + " " +
            df_erp["Thông số kỹ thuật"].fillna("") + " " +
            df_erp["search_string"].fillna("")
        ).apply(normalize)

        self.df_erp = df_erp
        self.erp_texts = df_erp["full_text"].tolist()

        self.vectorizer = TfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform(self.erp_texts)

    def suggest(self, name, spec="", top_n=1):

        query_raw = f"{name} {spec}"
        query_norm = normalize(query_raw)

        q_vec = self.vectorizer.transform([query_norm])

        base = cosine_similarity(q_vec, self.matrix).flatten()

        domain = detect_domain(query_raw)

        boosted_scores = []
        for i, base_score in enumerate(base):
            text = self.erp_texts[i]
            score = base_score
            score += part_number_boost(query_raw, text)
            score += size_boost(query_raw, text)
            score += material_boost(query_raw, text)
            score += domain_score(domain, text)
            boosted_scores.append(score)

        top_idx = sorted(range(len(boosted_scores)), key=lambda i: boosted_scores[i], reverse=True)[:top_n]

        results = []
        for idx in top_idx:
            row = self.df_erp.iloc[idx]
            results.append({
                "erp_code": row["Mã vật tư"],
                "similarity": float(round(boosted_scores[idx], 4)),
                "erp_name": row["Tên vật tư (NXT)"],
                "erp_spec": row["Thông số kỹ thuật"],
            })
        return results


# ============================================================
# 5. PIPELINE
# ============================================================

def run_pipeline():

    base = os.path.dirname(os.path.dirname(__file__))
    erp_file = os.path.join(base, "Data_For_Meili.xlsx")
    input_file = os.path.join(base, "Your_102_items.xlsx")
    output_file = os.path.join(base, "ERP_Suggestion_Output.xlsx")

    print("\nĐọc ERP master:", erp_file)
    df_erp = pd.read_excel(erp_file, engine="openpyxl")

    print("Đọc danh sách cần gợi ý:", input_file)
    df_new = pd.read_excel(input_file, engine="openpyxl")

    required_cols = ["STT", "Mã ERP", "Tên", "TS", "Đơn vị tính"]
    for c in required_cols:
        if c not in df_new.columns:
            raise ValueError(f"Thiếu cột bắt buộc trong input: {c}")

    engine = ERPSuggester(df_erp)

    all_rows = []

    print("\nBắt đầu xử lý...\n")

    for idx, row in df_new.iterrows():

        name = str(row["Tên"])
        spec = str(row["TS"])

        suggestion = engine.suggest(name, spec, top_n=1)[0]

        out = {
            "STT": row["STT"],
            "Mã ERP (gốc)": row["Mã ERP"],
            "Tên (input)": name,
            "TS (input)": spec,
            "Đơn vị tính": row["Đơn vị tính"],

            "erp_code": suggestion["erp_code"],
            "similarity": suggestion["similarity"],
            "erp_name": suggestion["erp_name"],
            "erp_spec": suggestion["erp_spec"],
        }

        all_rows.append(out)
        print(f"✓ {idx+1}/{len(df_new)} — {name}")

    df_out = pd.DataFrame(all_rows)
    df_out.to_excel(output_file, index=False)

    print(f"\n🎉 Hoàn tất! File xuất tại: {output_file}\n")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    run_pipeline()
