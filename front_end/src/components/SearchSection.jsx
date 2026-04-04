import React, { useState } from "react";
import api from "../constants/api_service";
import { 
  Search, Tag, Box, Ruler, AlertCircle, Cpu, 
  Zap, Layers, Loader2, Calendar, FileText, 
  DollarSign, ClipboardCheck, Info
} from "lucide-react";

const SearchSection = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState("combined");
  const [isFirstAiLoad, setIsFirstAiLoad] = useState(false);

  // --- 1. HÀM CHUẨN HÓA DỮ LIỆU (UNIFIED MAPPING) ---
  const formatResult = (item, engineType) => {
    if (engineType === "meili") {
      return {
        matchHeThong: item["Tên vật tư (NXT)"] || item["Tên vật tư"] || "N/A",
        erp: item["Mã vật tư"] || item.erp || "N/A",
        chung_loai: item["CHỦNG LOẠI"] || "Vật tư kỹ thuật",
        dvt: item["Đơn vị tính"] || "Cái",
        hang: item["Hãng sản xuất"] || "Không xác định",
        tskt: item["Diễn Giải"] || item["Thông số kỹ thuật"] || "N/A",
        don_gia: item["Đơn Giá Nhập"],
        hop_dong: item["Số Hợp Đồng/QĐ"],
        nam: item["Năm"],
        kho: item["Kho"],
        score: 100, 
        engine: "Core2 (Meili)",
        explain: { why: ["+Khớp chính xác mã hiệu"], isMeili: true }
      };
    }

    // Phần AI Semantic (Cổng 8000)
    return {
      matchHeThong: item.matchHeThong || "N/A",
      erp: item.erp || "N/A",
      chung_loai: item.chung_loai || "Vật tư khác",
      dvt: item.dvt || "Cái",
      hang: item.hang || item.brand || "Không xác định",
      tskt: item.ts || item.tskt || "Không có dữ liệu mô tả.",
      score: item.score || 0,
      engine: item.engine || "Legacy AI",
      explain: item.explain || { why: ["Phân tích ngữ nghĩa AI"] }
    };
  };

  // --- HÀM BỔ TRỢ: LẤY FULL DATA TỪ MEILI THEO DANH SÁCH ERP ---
  const fetchMetadataFromMeili = async (erpList) => {
    if (!erpList || erpList.length === 0) return [];
    try {
      // Tìm kiếm chính xác theo danh sách mã ERP
      const queries = erpList.map(erp => ({
        indexName: 'vattu', // Tên index của Hiếu
        q: erp,
        filter: `erp = "${erp}" OR "Mã vật tư" = "${erp}"`,
        limit: 1
      }));
      
      // Meilisearch hỗ trợ multi-search hoặc Hiếu có thể loop nhanh
      const results = await Promise.all(
        erpList.map(erp => api.searchMeilisearch(erp))
      );

      return results.map(res => res.hits[0]).filter(Boolean);
    } catch (err) {
      console.error("Lỗi truy vấn ngược Meili:", err);
      return [];
    }
  };

  // --- LOGIC TÌM KIẾM CẢI TIẾN ---
  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResults([]); 

    let finalResults = [];

    // BƯỚC 1: GỌI MEILI TRƯỚC (Ưu tiên chính xác)
    try {
      const meiliRes = await api.searchMeilisearch(query);
      if (meiliRes?.hits?.length > 0) {
        finalResults = meiliRes.hits.map(item => formatResult(item, "meili"));
        setResults([...finalResults]); 
      }
    } catch (err) { console.error(err); }

    // BƯỚC 2: GỌI AI SEMANTIC
    if (searchMode === "legacy" || searchMode === "combined") {
      setIsFirstAiLoad(true);
      try {
        const aiData = await api.searchQuery(query, searchMode);
        
        if (Array.isArray(aiData) && aiData.length > 0) {
          // Lọc ra các ERP mà Meili bước 1 chưa tìm thấy
          const existingErps = new Set(finalResults.map(r => r.erp));
          const newAiErps = aiData
            .filter(item => !existingErps.has(item.erp))
            .map(item => item.erp);

          // BƯỚC 3: TRUY VẤN NGƯỢC LẠI MEILI ĐỂ LẤY METADATA CHO KẾT QUẢ AI
          const aiMetadata = await fetchMetadataFromMeili(newAiErps);
          
          const aiFormatted = aiData
            .filter(item => !existingErps.has(item.erp))
            .map(item => {
              // Tìm dữ liệu "gia phả" từ Meili tương ứng với mã ERP này
              const meta = aiMetadata.find(m => (m["Mã vật tư"] || m.erp) === item.erp);
              
              // Hợp nhất: Lấy Score/Explain từ AI + Metadata từ Meili
              return {
                ...formatResult(item, "ai"), // Lấy logic AI cũ
                don_gia: meta?.["Đơn Giá Nhập"] || null,
                hop_dong: meta?.["Số Hợp Đồng/QĐ"] || null,
                nam: meta?.["Năm"] || null,
                kho: meta?.["Kho"] || null,
                // Ghi chú thêm để Hiếu biết đây là kết quả AI được bọc Metadata
                engine: "AI + Core2 Metadata" 
              };
            });

          setResults(prev => [...prev, ...aiFormatted]);
        }
      } catch (err) {
        console.error("AI Step Error:", err);
      } finally {
        setIsFirstAiLoad(false);
      }
    }
    setLoading(false);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 mb-20 animate-in fade-in duration-700">
      {/* HEADER */}
      <div className="mb-8 mt-10">
        <h2 className="text-4xl font-black text-slate-800 flex items-center gap-3 tracking-tight">
          <Search className="text-blue-600" size={38} /> Tìm kiếm vật tư ERP v3.0
        </h2>
        <p className="text-slate-500 mt-2 italic border-l-4 border-blue-500 pl-4 font-medium">
          Đang kết nối: Core2 (Meilisearch) + Legacy AI (Semantic BGE-M3).
        </p>
      </div>

      {/* SEARCH BOX */}
      <div className="bg-white p-3 rounded-3xl shadow-2xl border border-slate-100 mb-12 focus-within:ring-4 ring-blue-50 transition-all">
        <div className="flex gap-2 p-1.5 bg-slate-50 rounded-2xl mb-3">
          {[
            { id: "combined", name: "Tổng hợp", icon: <Layers size={14}/> },
            { id: "core2", name: "Core2 (Meili)", icon: <Zap size={14}/> },
            { id: "legacy", name: "AI Semantic", icon: <Cpu size={14}/> },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setSearchMode(m.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl transition-all font-black text-[11px] uppercase tracking-wider ${
                searchMode === m.id ? "bg-white shadow-md text-blue-600 scale-[1.02]" : "text-slate-400 hover:text-slate-600"
              }`}
            >
              {m.icon} {m.name}
            </button>
          ))}
        </div>

        <textarea
          className="w-full p-4 border-none focus:ring-0 text-xl text-slate-700 placeholder:text-slate-300 resize-none font-bold"
          rows="3"
          placeholder="Dán Mã hiệu, Part Number hoặc Mã ERP..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        <div className="flex justify-between items-center p-3 border-t border-slate-50">
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400 font-black uppercase pl-2">Engine: <span className="text-blue-500">{searchMode}</span></span>
            {isFirstAiLoad && loading && <span className="text-[9px] text-orange-500 pl-2 animate-pulse font-bold tracking-tighter">* AI ĐANG TÍCH PHÂN...</span>}
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-black py-3 px-12 rounded-2xl transition-all shadow-lg active:scale-95 disabled:bg-slate-200 flex items-center gap-3 uppercase tracking-widest text-sm"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <ClipboardCheck size={20} />}
            Tìm kiếm
          </button>
        </div>
      </div>

      {/* RESULTS */}
      <div className="space-y-8">
        {results.length === 0 && !loading && (
          <div className="text-center py-24 bg-slate-50 rounded-[40px] border-4 border-dashed border-slate-100">
            <Box size={60} className="mx-auto text-slate-200 mb-4" />
            <p className="text-slate-400 font-black uppercase tracking-widest">Hiếu nhập từ khóa để bắt đầu</p>
          </div>
        )}

        {results.map((item, index) => (
          <div key={index} className="bg-white border border-slate-100 p-8 rounded-[32px] shadow-sm hover:shadow-2xl transition-all duration-500 group relative overflow-hidden">
            {/* Tag Engine */}
            <div className={`absolute right-0 top-0 px-6 py-2 text-[10px] font-black text-white rounded-bl-3xl uppercase tracking-widest italic ${
                item.engine.includes("Meili") ? "bg-orange-600" : "bg-slate-900"
            }`}>
                {item.engine}
            </div>

            <div className="flex justify-between items-start mb-6">
              <div className="flex-1 mr-6">
                <div className="flex items-center gap-3 mb-2">
                  <span className="px-3 py-1 bg-blue-50 text-blue-600 text-[10px] font-black rounded-full uppercase border border-blue-100">Hạng {index + 1}</span>
                  {item.score >= 85 && <span className="px-3 py-1 bg-green-50 text-green-600 text-[10px] font-black rounded-full uppercase border border-green-100">Tin cậy cao</span>}
                </div>
                <h3 className="text-2xl font-black text-slate-800 leading-tight group-hover:text-blue-600 transition-colors">
                  {item.matchHeThong}
                </h3>
              </div>
              <div className={`px-6 py-3 rounded-3xl text-xl font-black shadow-inner flex flex-col items-center min-w-[100px] ${
                item.score >= 80 ? "bg-green-600 text-white" : "bg-orange-500 text-white"
              }`}>
                <span className="text-[9px] opacity-70 uppercase tracking-widest mb-1">Độ khớp</span>
                {item.score}%
              </div>
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 flex flex-col justify-center">
                <span className="text-[10px] text-slate-400 font-black uppercase mb-1">Mã ERP</span>
                <code className="text-blue-700 font-black text-sm cursor-copy hover:underline" onClick={() => copyToClipboard(item.erp)}>{item.erp}</code>
              </div>
              <div className="bg-green-50/30 p-4 rounded-2xl border border-green-100 flex flex-col justify-center">
                <span className="text-[10px] text-green-600 font-black uppercase mb-1 flex items-center gap-1"><DollarSign size={10}/> Giá nhập gần nhất</span>
                <span className="text-green-700 font-black text-base">{item.don_gia ? `${item.don_gia.toLocaleString()} VNĐ` : "---"}</span>
              </div>
              <div className="bg-orange-50/30 p-4 rounded-2xl border border-orange-100 flex flex-col justify-center">
                <span className="text-[10px] text-orange-600 font-black uppercase mb-1 flex items-center gap-1"><Calendar size={10}/> Năm / ĐVT</span>
                <span className="text-orange-700 font-black text-base">{item.nam || "---"} / {item.dvt}</span>
              </div>
              <div className="bg-purple-50/30 p-4 rounded-2xl border border-purple-100 flex flex-col justify-center overflow-hidden">
                <span className="text-[10px] text-purple-600 font-black uppercase mb-1 flex items-center gap-1"><FileText size={10}/> Hợp Đồng / QĐ</span>
                <span className="text-purple-700 font-bold text-[11px] truncate leading-tight" title={item.hop_dong}>{item.hop_dong || "N/A"}</span>
              </div>
            </div>

            {/* AI Explain & Trọng số */}
            {item.explain && typeof item.explain === 'object' && (
              <div className="mb-6 p-5 bg-slate-50 rounded-[24px] border border-slate-100">
                <div className="flex items-center gap-2 mb-4">
                  <Info size={14} className="text-blue-500" />
                  <span className="text-[10px] font-black uppercase text-slate-500 tracking-wider">Chi tiết thẩm định</span>
                </div>
                
                {/* Trọng số (Chỉ hiện nếu là AI) */}
                {!item.explain.isMeili && (
                  <div className="flex flex-wrap gap-3 mb-4">
                    <div className="bg-white px-3 py-1.5 rounded-xl border border-slate-200 text-[10px] font-bold">
                      <span className="text-slate-400 mr-2">CROSS:</span> {item.explain.weighted_cross || 0}
                    </div>
                    <div className="bg-white px-3 py-1.5 rounded-xl border border-slate-200 text-[10px] font-bold">
                      <span className="text-slate-400 mr-2">BI:</span> {item.explain.weighted_bi || 0}
                    </div>
                    <div className="bg-green-50 px-3 py-1.5 rounded-xl border border-green-200 text-[10px] font-black text-green-700">
                      BONUS: +{item.explain.bonus || 0}
                    </div>
                    {item.explain.penalty > 0 && (
                      <div className="bg-red-50 px-3 py-1.5 rounded-xl border border-red-200 text-[10px] font-black text-red-700">
                        PENALTY: -{item.explain.penalty}
                      </div>
                    )}
                  </div>
                )}

                {/* Tags giải thích */}
                {item.explain.why && (
                  <div className="flex flex-wrap gap-2">
                    {item.explain.why.map((reason, rIdx) => (
                      <span key={rIdx} className="px-2 py-1 bg-blue-600 text-white text-[9px] font-black rounded-lg uppercase tracking-tighter shadow-sm">
                        {reason}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Technical Specs */}
            <div className="bg-slate-900 text-slate-100 p-6 rounded-[24px] shadow-lg border-b-4 border-blue-600">
              <div className="flex items-center gap-2 mb-3 opacity-60">
                <AlertCircle size={14} />
                <span className="text-[10px] font-black uppercase tracking-[0.2em]">Thông số / Diễn giải kho</span>
              </div>
              <p className="text-[14px] leading-relaxed font-bold italic text-blue-100">
                {item.tskt}
              </p>
            </div>
            
            <div className="flex justify-between items-center text-[11px] font-bold text-slate-400 px-2 pt-4 italic">
                <span>Kho: {item.kho || "Không xác định"}</span>
                <span className="uppercase tracking-widest opacity-50">Vinh Tan 4 Thermal Power Plant</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchSection;