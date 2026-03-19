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
        Xử lý thẩm định hàng loạt từ dữ liệu Frontend gửi lên.
        """
        # 1. Chuẩn bị danh sách Query
        print(f"🔍 Đang xử lý Batch {len(raw_data)} items...") # THÊM DÒNG NÀY
        
        
        
        queries = []
        for d in raw_data:
            # Lấy tên và thông số, nếu không có thì để trống thay vì báo lỗi
            t = d.get('ten', '')
            ts = d.get('tskt', '')
            queries.append(f"{t} {ts}".strip())
        
        # 2. Gọi AI Search Batch (Xử lý song song trên CPU)
        all_matches = self.engine.search_batch(queries, top_k=1, explain=True)
        
        final_reports = []
        for i, matches in enumerate(all_matches):
            # Lấy dữ liệu gốc ban đầu
            word_item = raw_data[i]
            current_word_name = word_item.get('ten', '')
            
            if matches:
                # print(f"✅ Found match for: {queries[i][:30]}...") # THÊM DÒNG NÀY (Optional)
                
                best = matches[0]
                
                # Khớp với cấu trúc của engine.py (ma_vattu, ten_vattu)
                # Dùng .get() để nếu AI trả về thiếu key cũng không gây sập App
                stock_name = best.get('ten_vattu', best.get('ten', '---'))
                stock_ma = best.get('ma_vattu', best.get('ma', '---'))
                
                # Tính toán highlight sự khác biệt
                diff_html = self.highlight_diff(current_word_name, stock_name)
                
                final_reports.append({
                    "stt": word_item.get('stt', str(i+1)),
                    "word_name": current_word_name,
                    "stock_name": stock_name,
                    "dvt_he_thong": best.get('dvt', '---'),
                    "chung_loai": best.get('chung_loai', '---'),
                    "erp": stock_ma,
                    "score": round(best.get('final_score', 0), 2),
                    "explain": best.get('explain'), # THÊM DÒNG NÀY để đẩy về Frontend
                    "diff_html": diff_html,
                    "full_stock_info": best
                })
            else:
                print(f"❌ No match for: {queries[i][:30]}") # THÊM DÒNG NÀY
                # Trường hợp không khớp được món nào trong kho Vĩnh Tân 4
                final_reports.append({
                    "stt": word_item.get('stt', str(i+1)),
                    "word_name": current_word_name,
                    "stock_name": "--- Không tìm thấy trong kho ---",
                    "dvt_he_thong": "---",
                    "chung_loai": "---",
                    "erp": "---",
                    "score": round(best.get('final_score', 0), 2),
                    "explain": best.get('explain'), # THÊM DÒNG NÀY để đẩy về Frontend
                    "diff_html": diff_html,
                    "full_stock_info": best
                })
                
        return final_reports