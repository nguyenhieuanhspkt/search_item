import React, { useState } from "react";
import api from "../constants/api_service";
import { Search, Tag, Box, Ruler, AlertCircle, Cpu, Zap, Layers, Loader2 } from "lucide-react";

const SearchSection = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState("combined");
  const [isFirstAiLoad, setIsFirstAiLoad] = useState(false); // Theo dõi nạp AI lần đầu

  // Hàm xác định màu sắc chủng loại của Hiếu
  const getCategoryStyle = (cat) => {
    if (!cat || cat === "N/A" || cat === "Vật tư khác") {
      return "bg-slate-50 text-slate-400 border-slate-200 italic";
    }
    const normalizedCat = cat.trim();
    const styles = {
      "Vật liệu chịu lửa": "bg-orange-100 text-orange-700 border-orange-200",
      "Cơ khí - Kim loại": "bg-blue-100 text-blue-700 border-blue-200",
      "Thiết thiết bị điện": "bg-yellow-100 text-yellow-800 border-yellow-200",
      "Hóa chất - Dầu mỡ": "bg-purple-100 text-purple-700 border-purple-200",
      "Làm kín & Cách điện": "bg-teal-100 text-teal-700 border-teal-200",
      "Phụ tùng Bơm/Van": "bg-red-100 text-red-700 border-red-200",
    };
    return styles[normalizedCat] || "bg-indigo-50 text-indigo-600 border-indigo-100 border-dashed";
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    // Nếu chọn chế độ có AI (legacy/combined), nhắc người dùng có thể đợi lâu ở lần đầu
    if (searchMode !== "core2") {
        setIsFirstAiLoad(true);
    }

    try {
      const res = await api.searchQuery(query, searchMode);
      if (Array.isArray(res)) {
        setResults(res);
      } else {
        alert("Phản hồi từ Server không đúng định dạng.");
      }
    } catch (err) {
      console.error(err);
      alert("Lỗi kết nối Server. Vui lòng kiểm tra Backend.");
    } finally {
      setLoading(false);
      setIsFirstAiLoad(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in duration-700 px-4 mb-20">
      {/* HEADER */}
      <div className="mb-8">
        <h2 className="text-3xl font-black text-gray-800 flex items-center gap-3">
          <Search className="text-blue-600" size={32} /> Thẩm định đơn lẻ v2.6
        </h2>
        <p className="text-gray-500 mt-2 italic border-l-4 border-blue-200 pl-4">
          Hệ thống Unified: Ưu tiên mã hiệu kỹ thuật (Core2) & Bổ trợ ngữ nghĩa (AI).
        </p>
      </div>

      {/* SEARCH BOX */}
      <div className="bg-white p-2 rounded-2xl shadow-xl border border-gray-100 mb-10 transition-all focus-within:ring-2 ring-blue-100">
        {/* MODE SWITCHER */}
        <div className="flex gap-2 p-1.5 bg-slate-50 rounded-xl mb-2">
          {[
            { id: "combined", name: "Tổng hợp", icon: <Layers size={14}/>, desc: "Tốt nhất" },
            { id: "core2", name: "Core2 (Mã)", icon: <Zap size={14}/>, desc: "Siêu nhanh" },
            { id: "legacy", name: "AI Semantic", icon: <Cpu size={14}/>, desc: "Ngữ nghĩa" },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setSearchMode(m.id)}
              className={`flex-1 flex flex-col items-center py-2 rounded-lg transition-all ${
                searchMode === m.id 
                ? "bg-white shadow-sm text-blue-600 border border-blue-100" 
                : "text-gray-400 hover:text-gray-600"
              }`}
            >
              <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-wider">
                {m.icon} {m.name}
              </div>
              <span className="text-[9px] opacity-60 font-medium">{m.desc}</span>
            </button>
          ))}
        </div>

        <textarea
          className="w-full p-4 border-none focus:ring-0 text-lg text-gray-700 placeholder:text-gray-300 resize-none font-medium"
          rows="3"
          placeholder="Nhập tên vật tư, kích thước hoặc mã hiệu (VD: 6205-2RS, Vòng bi...)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSearch();
            }
          }}
        />

        <div className="flex justify-between items-center p-2 border-t border-gray-50">
          <div className="flex flex-col">
            <span className="text-[10px] text-gray-400 pl-2 uppercase font-bold">
                Engine: <span className="text-blue-500">{searchMode}</span>
            </span>
            {isFirstAiLoad && loading && (
                <span className="text-[9px] text-orange-500 pl-2 animate-pulse font-bold">
                    * Lần đầu nạp AI có thể mất 30-60s...
                </span>
            )}
          </div>
          
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-10 rounded-xl transition-all shadow-lg active:scale-95 disabled:bg-gray-300 flex items-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Zap size={18} />}
            {loading ? "Đang xử lý..." : "Thẩm định ngay"}
          </button>
        </div>
      </div>

      {/* RESULTS LIST */}
      <div className="space-y-6">
        {results.length === 0 && !loading && (
            <div className="text-center py-20 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                <Box size={48} className="mx-auto text-slate-300 mb-4" />
                <p className="text-slate-400 font-bold">Chưa có kết quả thẩm định nào.</p>
            </div>
        )}

        {results.map((item, index) => (
          <div
            key={index}
            className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 group relative overflow-hidden"
          >
            {/* SOURCE TAG */}
            <div className="absolute right-0 top-0 px-4 py-1.5 bg-slate-100 text-[9px] font-black text-slate-500 rounded-bl-2xl uppercase tracking-widest border-l border-b border-slate-200">
                {item.engine || "Hệ thống"}
            </div>

            {/* SIDE BAR COLOR */}
            <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${item.score >= 80 ? 'bg-green-500' : 'bg-orange-400'}`}></div>

            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Hạng {index + 1}</span>
                  {item.score >= 90 && (
                    <span className="text-[9px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold uppercase">Tin cậy cao</span>
                  )}
                </div>
                <h3 className="text-xl font-bold text-gray-800 group-hover:text-blue-700 transition-colors leading-tight">
                  {item.matchHeThong}
                </h3>
              </div>
              <div className="text-right ml-4">
                <div className={`px-4 py-2 rounded-2xl text-sm font-black shadow-sm flex flex-col items-center min-w-[80px] ${
                  item.score >= 80 ? "bg-green-600 text-white" : "bg-orange-500 text-white"
                }`}>
                  <span className="text-[9px] opacity-80 uppercase tracking-tighter">Độ chính xác</span>
                  <span className="text-lg">{item.score}%</span>
                </div>
              </div>
            </div>

            {/* EXPLAIN BOX */}
            {item.explain && (
              <div className="mb-5 flex items-start gap-3 bg-blue-50/40 p-3.5 rounded-xl border border-blue-100/50">
                <AlertCircle size={16} className="text-blue-500 mt-0.5 flex-shrink-0" />
                <div className="text-[12px] text-blue-800 leading-relaxed">
                  <span className="uppercase text-[10px] font-black opacity-60 block mb-1">Lý do khớp:</span>
                  <span className="font-semibold">
                    {typeof item.explain === 'object' 
                      ? `Độ tương đồng: ${item.score}% (Dựa trên: ${item.explain.why || 'Mã hiệu & Thông số'})`
                      : item.explain}
                  </span>
                </div>
              </div>
            )}
            {/* SPEC GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-y-4 gap-x-8 text-sm border-t border-gray-50 pt-5">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Box size={16} /></div>
                <div>
                    <span className="text-[11px] text-gray-400 font-bold block uppercase">Mã vật tư ERP</span>
                    <code className="text-blue-700 font-black text-sm">{item.erp}</code>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Tag size={16} /></div>
                <div>
                    <span className="text-[11px] text-gray-400 font-bold block uppercase">Chủng loại</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getCategoryStyle(item.chung_loai)}`}>
                        {item.chung_loai || "Vật tư khác"}
                    </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Ruler size={16} /></div>
                <div>
                    <span className="text-[11px] text-gray-400 font-bold block uppercase">Đơn vị tính</span>
                    <span className="font-bold text-gray-700">{item.dvt || "Bộ/Cái"}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-50 rounded-lg text-slate-400"><Zap size={16} /></div>
                <div>
                    <span className="text-[11px] text-gray-400 font-bold block uppercase">Hãng sản xuất</span>
                    <span className="font-bold text-gray-700">{item.hang || "Không xác định"}</span>
                </div>
              </div>

              {/* TECHNICAL DESCRIPTION - Phù hợp với mọi Key từ Backend */}
              <div className="col-span-1 md:col-span-2 mt-2 bg-slate-50/80 p-4 rounded-2xl border border-slate-100">
                <strong className="text-slate-400 block text-[10px] uppercase font-black tracking-widest mb-2">Thông số kỹ thuật trên ERP:</strong>
                <p className="text-gray-700 text-[13px] leading-relaxed font-semibold italic">
                  {item.ts || item.tskt || item.thong_so || "Không có dữ liệu mô tả chi tiết."}
                </p>
              </div>
            </div>

            {/* PROGRESS BAR */}
            <div className="w-full bg-gray-100 h-1.5 rounded-full mt-6 overflow-hidden">
              <div
                className={`h-full transition-all duration-1000 ${
                  item.score >= 80 ? "bg-green-500" : "bg-orange-400"
                }`}
                style={{ width: `${item.score}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchSection;