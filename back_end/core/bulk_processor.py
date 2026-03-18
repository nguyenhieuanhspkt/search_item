import difflib
# Import cái engine mà chúng ta đã vất vả tối ưu ở Bước 2
try:
    from engine import HybridSearchEngine
except ImportError:
    from .engine import HybridSearchEngine

class BulkMatcher:
    def __init__(self, engine: HybridSearchEngine):
        """
        Nhận vào instance của HybridSearchEngine đã được khởi tạo
        để không phải load lại model AI (tránh tốn RAM)
        """
        self.engine = engine

    def highlight_diff(self, word_str, stock_str):
        """So sánh và tô màu Xanh/Đỏ sự khác biệt"""
        s = difflib.SequenceMatcher(None, word_str, stock_str)
        res = []
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            if tag == 'equal':
                res.append(word_str[i1:i2])
            elif tag == 'replace':
                res.append(f"<span style='color:red;text-decoration:line-through'>{word_str[i1:i2]}</span>")
                res.append(f"<span style='color:green;font-weight:bold'>{stock_str[j1:j2]}</span>")
            elif tag == 'delete':
                res.append(f"<span style='color:red;text-decoration:line-through'>{word_str[i1:i2]}</span>")
            elif tag == 'insert':
                res.append(f"<span style='color:green;font-weight:bold'>{stock_str[j1:j2]}</span>")
        return "".join(res)

    def process_data(self, raw_data):
        """
        Hàm xử lý chính: 
        1. Gom queries
        2. Gọi search_batch
        3. Diff & Report
        """
        # Chuẩn bị input cho AI: Kết hợp Tên + Thông số kỹ thuật
        queries = [f"{d['ten']} {d['tskt']}" for d in raw_data]
        
        # Gọi hàm search_batch thần thánh của ông
        all_matches = self.engine.search_batch(queries, top_k=1)
        
        final_reports = []
        for i, matches in enumerate(all_matches):
            word_item = raw_data[i]
            
            if matches:
                best = matches[0]
                # Tạo bản báo cáo so sánh
                diff_html = self.highlight_diff(word_item['ten'], best['ten'])
                
                final_reports.append({
                    "stt": word_item['stt'],
                    "word_name": word_item['ten'],
                    "stock_name": best['ten'],
                    "dvt_he_thong": best.get('dvt'), # Thêm
                    "chung_loai": best.get('chung_loai'), # Thêm
                    "erp": best.get('ma'), # Thêm
                    "score": round(best['final_score'], 2),
                    "full_stock_info": best # Trả về full để hiện chi tiết nếu cần
                })
            else:
                final_reports.append({
                    "stt": word_item['stt'],
                    "word_name": word_item['ten'],
                    "score": 0,
                    "diff_html": "Không tìm thấy trong kho chuẩn"
                })
                
        return final_reports