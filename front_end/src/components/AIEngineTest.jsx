import React, { useState } from "react";
import api from "../constants/api_service"; // Sử dụng object api mặc định

const AIEngineTest = () => {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  // Khởi tạo state với cấu trúc mặc định để tránh lỗi "undefined" khi render
  const [data, setData] = useState({
    ai_analysis: { brand: "", model: [], materials: [], specs: {} },
    results: [],
  });

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      // Gọi qua object api đã thống nhất ở api_service.js
      const response = await api.searchV2(query);

      // Kiểm tra nếu có dữ liệu trả về thì mới set, không thì giữ mặc định
      if (response && !response.error) {
        setData(response);
      } else {
        console.error("Lỗi từ server:", response?.error);
      }
    } catch (err) {
      console.error("Lỗi thực thi search:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-2 w-full bg-white">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-purple-700 flex items-center gap-2">
          🚀 AI Lab: Engine 2 (Inference Mode)
        </h2>
        <p className="text-sm text-gray-500 italic">
          Thử nghiệm bóc tách Model & Brand từ kho vật tư Vĩnh Tân 4
        </p>
      </div>

      {/* Form tìm kiếm */}
      <form onSubmit={handleSearch} className="flex gap-2 mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Nhập mã hiệu hoặc mô tả vật tư..."
          className="flex-1 p-3 border-2 border-purple-100 rounded-lg outline-none focus:border-purple-500 transition-all"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-purple-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-purple-700 disabled:bg-gray-400"
        >
          {loading ? "Đang phân tích..." : "PHÂN TÍCH AI"}
        </button>
      </form>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* CỘT TRÁI: KẾT QUẢ AI BÓC TÁCH */}
        <div className="lg:col-span-1 space-y-4">
          <div className="p-4 bg-purple-50 rounded-xl border border-purple-100 shadow-sm">
            <h3 className="font-bold text-purple-800 mb-3 border-b border-purple-200 pb-1">
              🔍 AI Bóc tách
            </h3>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-gray-400 uppercase">
                  Hãng sản xuất
                </label>
                <div className="text-lg font-bold text-gray-800">
                  {data?.ai_analysis?.brand || (
                    <span className="text-gray-300 italic">Không rõ</span>
                  )}
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-gray-400 uppercase">
                  Mã hiệu (Model)
                </label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {data?.ai_analysis?.model?.length > 0 ? (
                    data.ai_analysis.model.map((m, i) => (
                      <span
                        key={i}
                        className="bg-white border border-purple-200 text-purple-700 px-2 py-0.5 rounded text-xs font-mono"
                      >
                        {m}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-300">---</span>
                  )}
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-gray-400 uppercase">
                  Vật liệu
                </label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {data?.ai_analysis?.materials?.length > 0 ? (
                    data.ai_analysis.materials.map((m, i) => (
                      <span
                        key={i}
                        className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded text-[11px]"
                      >
                        {m}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-300">---</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CỘT PHẢI: KẾT QUẢ TÌM KIẾM TRONG KHO */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="p-3 text-xs font-bold text-gray-600">
                    Vật tư / Thông số
                  </th>
                  <th className="p-3 text-xs font-bold text-gray-600">Hãng</th>
                  <th className="p-3 text-xs font-bold text-gray-600 text-center">
                    Khớp
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data?.results?.map((item, idx) => (
                  <tr
                    key={idx}
                    className="hover:bg-gray-50 transition-colors text-sm"
                  >
                    <td className="p-3">
                      <div className="font-bold text-gray-800 uppercase">
                        {item.ten_vattu}
                      </div>
                      <div className="text-xs text-gray-500 font-mono">
                        {item.ma_vattu}
                      </div>
                      <div className="text-[11px] text-gray-400 italic mt-1">
                        {item.thong_so}
                      </div>
                    </td>
                    <td className="p-3 text-gray-600 font-medium">
                      {item.hang_sx}
                    </td>
                    <td className="p-3 text-center">
                      <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded-full text-[10px] font-black">
                        {item.final_score?.toFixed(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!data?.results || data.results.length === 0) && !loading && (
              <div className="p-10 text-center text-gray-300 italic">
                Nhập query để bắt đầu phân tích...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIEngineTest;
