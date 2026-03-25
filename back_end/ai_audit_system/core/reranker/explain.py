class AuditExplainer:
    def generate(self, q_feat, m_feat, final_score, threshold):
        common_models = set(q_feat["MODEL"]) & set(m_feat["MODEL"])
        common_brands = set(q_feat["BRAND"]) & set(m_feat["BRAND"])
        
        status = "🔴 KHÔNG TƯƠNG THÍCH"
        if final_score >= 0.95:
            status = "✅ XÁC NHẬN KHỚP"
        elif final_score >= threshold:
            status = "🟡 KHUYẾN NGHỊ KIỂM TRA"

        output = [
            f"KẾT LUẬN: {status}",
            f"MÃ HIỆU: {', '.join(common_models) if common_models else 'N/A'}",
            f"NHÃN HIỆU: {', '.join(common_brands) if common_brands else 'N/A'}",
            f"THÔNG SỐ KHỚP: {', '.join(set(q_feat['SPECS']) & set(m_feat['SPECS']))}",
            f"ĐỘ TIN CẬY: {int(final_score*100)}%"
        ]
        return "\n".join(output)