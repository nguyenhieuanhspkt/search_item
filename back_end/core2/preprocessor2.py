import re
from typing import List
from .schemas import Candidate

KEY_VALUE_PATTERN = re.compile(r"(.+?):\s*(.+)", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"(\d[\d\s\.,]*)(°C|mm|kg|%|A|V|W)?", re.IGNORECASE)

def run(text: str) -> List[Candidate]:
    text = text.strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    candidates = []

    # 1. Tên sản phẩm = dòng đầu tiên
    if lines:
        candidates.append(Candidate(
            raw_text=lines[0],
            normalized=lines[0],
            type_hint="product_name"
        ))
        lines = lines[1:]

    # 2. Lặp từng dòng
    for line in lines:
        # dạng key: value
        kv = KEY_VALUE_PATTERN.match(line)
        if kv:
            key, value = kv.groups()
            candidates.append(Candidate(
                raw_text=line,
                normalized=f"{key}:{value}",
                type_hint="attribute",
                meta={"key": key.strip(), "value": value.strip()}
            ))
            continue

        # dạng thông số có số liệu
        if NUMBER_PATTERN.search(line):
            candidates.append(Candidate(
                raw_text=line,
                normalized=line,
                type_hint="spec"
            ))
            continue

        # còn lại xem như text mô tả
        candidates.append(Candidate(
            raw_text=line,
            normalized=line,
            type_hint="text"
        ))

    return candidates