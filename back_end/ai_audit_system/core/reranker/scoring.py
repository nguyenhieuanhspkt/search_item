class AuditScorer:
    def __init__(self, weights):
        self.w = weights # Load từ weights.yaml

    def calculate(self, q_feat, m_feat, base_ai_score):
        score = base_ai_score * 0.4 # Giảm trọng số của AI gốc
        
        # 1. Match Model (Tuyệt đối)
        common_models = set(q_feat["MODEL"]) & set(m_feat["MODEL"])
        if q_feat["MODEL"]:
            if common_models:
                score += self.w.get('model_match', 0.5)
            else:
                score -= 0.8 # Phạt cực nặng nếu có model mà không khớp
        
        # 2. Match Brand
        common_brands = set(q_feat["BRAND"]) & set(m_feat["BRAND"])
        if common_brands:
            score += self.w.get('brand_match', 0.2)
            
        # 3. Match Specs & Name
        common_specs = set(q_feat["SPECS"]) & set(m_feat["SPECS"])
        score += len(common_specs) * self.w.get('spec_bonus', 0.05)
        
        return min(max(score, 0), 1.0) # Đưa về dải 0 -> 1