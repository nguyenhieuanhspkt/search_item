import React, { useState } from "react";
import api from "../constants/api_service";
import { Search, Tag, Box, Ruler, AlertCircle } from "lucide-react";

const SearchSection = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // Cập nhật hàm xác định màu sắc thông minh hơn
  const getCategoryStyle = (cat) => {
    if (!cat || cat === "N/A" || cat === "Vật tư khác") {
      return "bg-slate-50 text-slate-400 border-slate-200 italic";
    }

    // Chuẩn hóa chuỗi để so khớp (bỏ khoảng trắng, viết thường)
    const normalizedCat = cat.trim();

    const styles = {
      "Vật liệu chịu lửa": "bg-orange-100 text-orange-700 border-orange-200",
      "Cơ khí - Kim loại": "bg-blue-100 text-blue-700 border-blue-200",
      "Thiết bị điện": "bg-yellow-100 text-yellow-800 border-yellow-200",
      "Hóa chất - Dầu mỡ": "bg-purple-100 text-purple-700 border-purple-200",
      "Làm kín & Cách điện": "bg-teal-100 text-teal-700 border-teal-200",
      "Phụ tùng Bơm/Van": "bg-red-100 text-red-700 border-red-200",
    };

    // Nếu không khớp chính xác danh sách trên, trả về màu Indigo nhạt cho các chủng loại mới từ AI
    return styles[normalizedCat] || "bg-indigo-50 text-indigo-600 border-indigo-100 border-dashed";
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResults([]); 
    
    try {
      const res = await api.searchQuery(query);
      if (Array.isArray(res)) {
        setResults(res);
      } else {
        console.error("Lỗi API:", res);
        alert("Có lỗi xảy ra khi kết nối server.");
      }
    } catch (err) {
      alert("Lỗi hệ thống.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in duration-700 px-4">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-gray-800 flex items-center gap-3">
          <Search className="text-blue-600" size={32} /> Thẩm định vật tư đơn lẻ
        </h2>
        <p className="text-gray-500 mt-2 italic border-l-4 border-blue-200 pl-4">
          Hệ thống AI tự động phân loại chủng loại dựa trên danh mục ERP Vĩnh Tân 4.
        </p>
      </div>

      <div className="bg-white p-2 rounded-2xl shadow-xl border border-gray-100 mb-10 focus-within:border-blue-300 transition-all">
        <textarea
          className="w-full p-4 border-none focus:ring-0 text-lg text-gray-700 placeholder:text-gray-300 resize-none"
          rows="3"
          placeholder="Nhập tên vật tư hoặc mã hiệu kỹ thuật..."
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
          <span className="text-[10px] text-gray-400 pl-2">Nhấn Enter để tìm nhanh</span>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-8 rounded-xl transition-all shadow-lg active:scale-95 disabled:bg-gray-300 flex items-center gap-2"
          >
            {loading ? "⌛ Đang tìm..." : "🚀 Thẩm định"}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {results.map((item, index) => (
          <div
            key={index}
            className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 group relative overflow-hidden"
          >
            {/* Thanh màu chỉ thị nhanh bên trái card */}
            <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${item.score >= 80 ? 'bg-green-500' : 'bg-orange-400'}`}></div>

            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Top {index + 1}</span>
                  {item.score >= 95 && <span className="text-[9px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-bold uppercase">Khớp tuyệt đối</span>}
                </div>
                <h3 className="text-xl font-bold text-gray-800 group-hover:text-blue-700 transition-colors leading-tight">
                  {item.matchHeThong}
                </h3>
              </div>
              <div className="text-right ml-4">
                <div className={`px-4 py-1.5 rounded-xl text-sm font-black shadow-sm flex flex-col items-center ${
                  item.score >= 80 ? "bg-green-500 text-white" : "bg-orange-400 text-white"
                }`}>
                  <span className="text-[10px] opacity-80 uppercase">Độ tin cậy</span>
                  <span>{item.score}%</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm border-t border-gray-100 pt-4">
              <div className="flex items-center gap-2">
                <Box size={16} className="text-gray-400" />
                <strong className="text-gray-600 min-w-[80px]">Mã ERP:</strong>
                <code className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-bold text-xs">{item.erp}</code>
              </div>
              
              <div className="flex items-center gap-2">
                <Tag size={16} className="text-gray-400" />
                <strong className="text-gray-600 min-w-[80px]">Chủng loại:</strong>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-colors ${getCategoryStyle(item.chung_loai)}`}>
                  {item.chung_loai || "Chưa phân loại"}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <Ruler size={16} className="text-gray-400" />
                <strong className="text-gray-600 min-w-[80px]">ĐVT:</strong>
                <span className="font-bold text-gray-700">{item.dvt}</span>
              </div>

              {item.hang && (
                <div className="flex items-center gap-2">
                  <AlertCircle size={16} className="text-gray-400" />
                  <strong className="text-gray-600 min-w-[80px]">Hãng SX:</strong>
                  <span className="font-medium text-gray-700">{item.hang}</span>
                </div>
              )}

              <div className="col-span-1 md:col-span-2 mt-2 bg-slate-50 p-4 rounded-xl border border-slate-100">
                <strong className="text-slate-500 block text-[11px] uppercase tracking-wide mb-2">Thông số kỹ thuật ERP:</strong>
                <p className="text-gray-700 whitespace-pre-line leading-relaxed font-medium">
                  {item.ts || "Không có mô tả chi tiết."}
                </p>
              </div>
            </div>

            {/* Thanh Progress trực quan */}
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