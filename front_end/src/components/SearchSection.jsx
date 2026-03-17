// src/components/SearchSection.jsx
import React, { useState } from "react";
import api from "../constants/api_service";

const SearchSection = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query) return;
    setLoading(true);
    const res = await api.searchQuery(query);
    if (Array.isArray(res)) {
      setResults(res);
    } else {
      alert(res.error || "Không có kết quả");
    }
    setLoading(false);
  };

  return (
    <div className="animate-fade-in">
      <h2 className="text-3xl font-bold text-gray-800 mb-6">
        🔍 Thẩm định vật tư đơn lẻ
      </h2>

      <textarea
        className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-0 transition-all mb-4"
        rows="4"
        placeholder="VD: Bulong neo M24x600..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <button
        onClick={handleSearch}
        disabled={loading}
        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg transition-all shadow-lg active:scale-95 disabled:bg-gray-400"
      >
        {loading ? "⌛ Đang xử lý..." : "🚀 Thẩm định ngay"}
      </button>

      <div className="mt-10 space-y-4">
        {results.map((item, index) => (
          <div
            key={index}
            className="bg-white border border-gray-100 p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-blue-800">
                Top {index + 1}: {item.ten}
              </h3>
              <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-bold">
                Khớp: {item.final_score}%
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <p>
                <strong>Mã ERP:</strong>{" "}
                <code className="bg-gray-100 px-1 italic">{item.erp}</code>
              </p>
              <p>
                <strong>ĐVT:</strong> {item.dvt}
              </p>
              <p className="col-span-2 text-gray-600">
                <strong>Thông số:</strong> {item.ts}
              </p>
            </div>
            {/* Progress bar giả lập độ tin cậy giống Streamlit */}
            <div className="w-full bg-gray-200 h-2 rounded-full mt-4">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${item.final_score}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchSection;
