import React, { useState } from "react";
import api from "../constants/api_service";
import { 
  Search, Tag, Box, Ruler, AlertCircle, Cpu, 
  Zap, Layers, Loader2, Calendar, FileText, 
  DollarSign, ClipboardCheck 
} from "lucide-react";

const SearchSection = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState("combined");
  const [isFirstAiLoad, setIsFirstAiLoad] = useState(false);

  // --- 1. HÀM CHUẨN HÓA DỮ LIỆU (MAPPING TỪ SERVER 7700) ---
  const formatResult = (item, engineType) => {
    if (engineType === "meili") {
      const meiliScore = item._rankingScore ? Math.round(item._rankingScore * 100) : 100;
      
      // Hàm bóc dữ liệu không phân biệt hoa thường và dấu cách
      const getVal = (possibleKeys) => {
        const foundKey = Object.keys(item).find(k => 
          possibleKeys.some(pk => k.toLowerCase().trim() === pk.toLowerCase().trim())
        );
        return item[foundKey];
      };

      return {
        // Thông tin hiển thị chính
        matchHeThong: getVal(["Tên vật tư (NXT)", "Tên vật tư", "matchHeThong"]) || "Không rõ tên",
        erp: getVal(["Mã vật tư", "erp"]) || "N/A",
        chung_loai: getVal(["CHỦNG LOẠI", "Chủng loại"]) || "Vật tư kỹ thuật",
        dvt: getVal(["Đơn vị tính", "ĐVT"]) || "Cái",
        hang: getVal(["Hãng sản xuất", "Hãng SX"]) || "Không xác định",
        
        // Báu vật mới: Thông số kỹ thuật và Diễn giải
        tskt: getVal(["Thông số kỹ thuật", "Diễn Giải", "tskt"]) || "Dữ liệu đang được cập nhật...",
        
        // Thông tin quản lý kho & giá
        don_gia: getVal(["Đơn Giá Nhập", "Đơn giá"]),
        hop_dong: getVal(["Số Hợp Đồng/QĐ", "Số HĐ"]),
        nam: getVal(["Năm"]),
        kho: getVal(["Kho"]),
        
        score: meiliScore, 
        engine: "Core2 (Meili)",
        explain: "Dữ liệu khớp chính xác từ kho lưu trữ Meilisearch 2 vạn dòng."
      };
    }

    // Phần AI Semantic (Dữ liệu từ Backend cổng 8000)
    let aiExplain = "Phân tích ngữ nghĩa AI.";
    if (item.explain) {
      aiExplain = typeof item.explain === 'object' ? (item.explain.why || aiExplain) : item.explain;
    }

    return {
      matchHeThong: item.matchHeThong || "Không rõ tên",
      erp: item.erp || "N/A",
      chung_loai: item.chung_loai || "Vật tư khác",
      dvt: item.dvt || "Cái",
      hang: item.hang || "Không xác định",
      tskt: item.ts || item.tskt || "Không có dữ liệu mô tả.",
      score: item.score || 0,
      engine: item.engine || "Legacy AI",
      explain: aiExplain
    };
  };

  // --- 2. LOGIC TÌM KIẾM ---
  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResults([]); // Xóa kết quả cũ

    let meiliResults = [];

    // 1. GỌI MEILISEARCH (Chạy cực nhanh - Ưu tiên hiện trước)
    if (searchMode === "core2" || searchMode === "combined") {
      try {
        const searchResponse = await api.searchMeilisearch(query);
        if (searchResponse?.hits?.length > 0) {
          meiliResults = searchResponse.hits.map(item => formatResult(item, "meili"));
          setResults(meiliResults); // HIỆN NGAY KẾT QUẢ MEILI
        }
      } catch (err) {
        console.error("Meili Error:", err);
      }
    }

    // 2. GỌI AI BACKEND (Chạy chậm - Hiện sau hoặc bổ sung vào danh sách)
    if (searchMode === "legacy" || searchMode === "combined") {
      setIsFirstAiLoad(true);
      try {
        const aiData = await api.searchQuery(query, searchMode);
        if (Array.isArray(aiData) && aiData.length > 0) {
          const aiFormatted = aiData.map(item => formatResult(item, "ai"));
          
          // Lọc trùng ERP với Meili đã hiện
          const existingErps = new Set(meiliResults.map(r => r.erp));
          const uniqueAiRes = aiFormatted.filter(item => !existingErps.has(item.erp));
          
          // Cập nhật thêm kết quả AI vào danh sách đã có
          setResults(prev => [...prev, ...uniqueAiRes]);
        }
      } catch (err) {
        console.error("AI Error (Timeout):", err);
        // Nếu chỉ tìm bằng AI mà lỗi thì mới báo, còn Combined thì kệ nó
        if (searchMode === "legacy") alert("AI đang bận, Hiếu thử lại sau nhé!");
      } finally {
        setIsFirstAiLoad(false);
      }
    }

    setLoading(false);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // Có thể thêm toast notification ở đây
  };

  return (
    <div className="max-w-5xl mx-auto px-4 mb-20 animate-in fade-in duration-700">
      {/* HEADER SECTION */}
      <div className="mb-8 mt-10">
        <h2 className="text-4xl font-black text-slate-800 flex items-center gap-3 tracking-tight">
          <Search className="text-blue-600" size={38} /> Thẩm định Unified v3.0
        </h2>
        <p className="text-slate-500 mt-2 italic border-l-4 border-blue-500 pl-4 font-medium">
          Dữ liệu đồng bộ: 20,000+ vật tư Vĩnh Tân 4 (Full Metadata).
        </p>
      </div>

      {/* SEARCH BOX */}
      <div className="bg-white p-3 rounded-3xl shadow-2xl border border-slate-100 mb-12 transition-all focus-within:ring-4 ring-blue-50">
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
            {isFirstAiLoad && loading && <span className="text-[9px] text-orange-500 pl-2 animate-pulse font-bold tracking-tighter">* AI ĐANG PHÂN TÍCH...</span>}
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-black py-3 px-12 rounded-2xl transition-all shadow-lg active:scale-95 disabled:bg-slate-200 flex items-center gap-3 uppercase tracking-widest text-sm"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <ClipboardCheck size={20} />}
            Thẩm định
          </button>
        </div>
      </div>

      {/* RESULTS LIST */}
      <div className="space-y-8">
        {results.length === 0 && !loading && (
          <div className="text-center py-24 bg-slate-50 rounded-[40px] border-4 border-dashed border-slate-100">
            <Box size={60} className="mx-auto text-slate-200 mb-4" />
            <p className="text-slate-400 font-black uppercase tracking-widest">Không tìm thấy vật tư phù hợp</p>
          </div>
        )}

        {results.map((item, index) => (
          <div key={index} className="bg-white border border-slate-100 p-8 rounded-[32px] shadow-sm hover:shadow-2xl transition-all duration-500 group relative overflow-hidden">
            {/* Tag Engine */}
            <div className="absolute right-0 top-0 px-6 py-2 bg-slate-900 text-[10px] font-black text-white rounded-bl-3xl uppercase tracking-[0.2em] italic">
                {item.engine}
            </div>

            <div className="flex justify-between items-start mb-6">
              <div className="flex-1 mr-6">
                <div className="flex items-center gap-3 mb-2">
                  <span className="px-3 py-1 bg-blue-50 text-blue-600 text-[10px] font-black rounded-full uppercase">Hạng {index + 1}</span>
                  {item.score >= 90 && <span className="px-3 py-1 bg-green-50 text-green-600 text-[10px] font-black rounded-full uppercase">Tin cậy cao</span>}
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
                <span className="text-[10px] text-slate-400 font-black uppercase mb-1">Mã vật tư ERP</span>
                <code className="text-blue-700 font-black text-sm cursor-copy hover:underline" onClick={() => copyToClipboard(item.erp)}>{item.erp}</code>
              </div>
              <div className="bg-green-50/30 p-4 rounded-2xl border border-green-100 flex flex-col justify-center">
                <span className="text-[10px] text-green-600/60 font-black uppercase mb-1 flex items-center gap-1"><DollarSign size={10}/> Đơn giá nhập</span>
                <span className="text-green-700 font-black text-base">{item.don_gia ? `${item.don_gia.toLocaleString()} VNĐ` : "---"}</span>
              </div>
              <div className="bg-orange-50/30 p-4 rounded-2xl border border-orange-100 flex flex-col justify-center">
                <span className="text-[10px] text-orange-600/60 font-black uppercase mb-1 flex items-center gap-1"><Calendar size={10}/> Năm / ĐVT</span>
                <span className="text-orange-700 font-black text-base">{item.nam || "---"} / {item.dvt}</span>
              </div>
              <div className="bg-purple-50/30 p-4 rounded-2xl border border-purple-100 flex flex-col justify-center overflow-hidden">
                <span className="text-[10px] text-purple-600/60 font-black uppercase mb-1 flex items-center gap-1"><FileText size={10}/> Số Hợp Đồng</span>
                <span className="text-purple-700 font-bold text-[11px] truncate leading-tight" title={item.hop_dong}>{item.hop_dong || "N/A"}</span>
              </div>
            </div>

            {/* Technical Specs - The Star of v3.0 */}
            <div className="space-y-4">
              <div className="bg-slate-900 text-slate-100 p-6 rounded-[24px] shadow-lg border-b-4 border-blue-600">
                <div className="flex items-center gap-2 mb-3 opacity-60">
                  <AlertCircle size={14} />
                  <span className="text-[10px] font-black uppercase tracking-[0.2em]">Thông số kỹ thuật & Diễn giải</span>
                </div>
                <p className="text-[14px] leading-relaxed font-bold italic text-blue-100">
                  {item.tskt}
                </p>
              </div>
              
              <div className="flex justify-between items-center text-[11px] font-bold text-slate-400 px-2 pt-2">
                <div className="flex items-center gap-2 italic">
                   <Box size={14} /> <span>Kho: {item.kho || "Chưa xác định"}</span>
                </div>
                <div className="uppercase tracking-widest opacity-50">Vinh Tan 4 Thermal Power Plant</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchSection;