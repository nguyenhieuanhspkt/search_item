import React from "react";
import { Eye, Tag, Box, AlertCircle } from "lucide-react";

const PreviewTable = ({ data, isResult, loading }) => {
  if (!loading && data.length === 0) return null;

  /**
   * Hàm xác định màu sắc cho Chủng loại
   * Ưu tiên các nhóm chính tại Vĩnh Tân 4, còn lại dùng màu xám dự phòng
   */
  const getCategoryStyle = (cat) => {
    if (!cat || cat === "N/A" || cat === "Vật tư khác") {
      return "bg-slate-50 text-slate-500 border-slate-200 italic";
    }

    const fixedStyles = {
      "Vật liệu chịu lửa": "bg-orange-100 text-orange-700 border-orange-200",
      "Cơ khí - Kim loại": "bg-blue-100 text-blue-700 border-blue-200",
      "Thiết bị điện": "bg-yellow-100 text-yellow-800 border-yellow-200",
      "Hóa chất - Dầu mỡ": "bg-purple-100 text-purple-700 border-purple-200",
      "Làm kín & Cách điện": "bg-teal-100 text-teal-700 border-teal-200",
      "Phụ tùng Bơm/Van": "bg-red-100 text-red-700 border-red-200",
    };

    // Nếu là nhóm mới chưa định nghĩa màu cụ thể
    return fixedStyles[cat] || "bg-indigo-50 text-indigo-600 border-indigo-100 border-dashed";
  };

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden animate-in fade-in slide-in-from-top-2 duration-500">
      {/* Header Bảng */}
      <div className="px-6 py-4 border-b border-gray-50 bg-gray-50/30 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Eye size={18} className="text-gray-400" />
          <span className="font-bold text-gray-700 text-sm">
            {isResult ? "Kết quả thẩm định AI" : "Xem trước dữ liệu trích xuất"}
          </span>
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-xs text-blue-600 animate-pulse font-medium">
            <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
            Đang xử lý...
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 text-gray-600 text-[11px] uppercase tracking-wider font-bold">
              <th className="p-4 text-center w-12">STT</th>
              <th className="p-4 text-left">Vật tư (Word)</th>
              <th className="p-4 text-left">Thông số kỹ thuật (Word)</th>
              <th className="p-4 text-center">ĐVT (Word)</th> {/* THÊM CỘT NÀY */}
              <th className="p-4 text-left text-blue-600">👉 Vật tư khớp nhất (VT4)</th>
              <th className="p-4 text-center">Mã ERP</th>
              <th className="p-4 text-center">ĐVT (ERP)</th>
              <th className="p-4 text-center">Độ tin cậy</th>
            </tr>
          </thead>

          <tbody>
            {data.map((item, idx) => (
              <tr key={idx} className="border-b border-gray-50 hover:bg-blue-50/40 transition-all">
                <td className="p-4 text-center text-gray-400 text-xs">{item.stt}</td>
                
                {/* 1. Tên từ Word */}
                <td className="p-4 font-semibold text-gray-800 text-sm w-[200px]">
                  {item.ten}
                </td>

                {/* 2. Thông số từ Word - Tách riêng giúp bảng thoáng hơn */}
                <td className="p-4 text-[11px] text-gray-500 max-w-[250px] italic">
                  {item.ts || "---"}
                </td>

                {/* 3. ĐVT từ Word */}
                <td className="p-4 text-center text-sm font-medium text-orange-600">
                  {item.dvt_word || item.dvt || "---"}
                </td>

                {/* 4. Kết quả AI (Xanh Đỏ) */}
                <td className="p-4">
                  <div 
                    className="text-sm leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: item.diff_html || item.matchHeThong || "---" }} 
                  />
                </td>

                {/* 5. Mã ERP */}
                <td className="p-4 text-center">
                  <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded font-mono text-[11px] font-bold">
                    {item.erp || "---"}
                  </span>
                </td>

                {/* 6. ĐVT chuẩn ERP */}
                <td className="p-4 text-center text-sm font-bold text-blue-800">
                  {item.dvt_he_thong || "---"}
                </td>

                {/* 7. Score */}
                <td className="p-4 text-center">
                  <span className={`font-black text-sm ${
                    item.score >= 0.8 ? 'text-green-600' : 
                    item.score >= 0.5 ? 'text-orange-500' : 'text-red-500'
                  }`}>
                    {item.score ? (item.score * 100).toFixed(1) + "%" : "0%"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer Ghi chú */}
      {isResult && (
        <div className="px-6 py-3 bg-gray-50/80 border-t border-gray-100 flex justify-between items-center">
          <p className="text-[10px] text-gray-400 italic">
            * Dữ liệu đối soát dựa trên danh mục ERP nhà máy cập nhật mới nhất.
          </p>
          <div className="flex gap-3">
            <div className="flex items-center gap-1 text-[10px] text-gray-500">
               <div className="w-2 h-2 bg-green-500 rounded-full"></div> Khớp tốt
            </div>
            <div className="flex items-center gap-1 text-[10px] text-gray-500">
               <div className="w-2 h-2 bg-rose-500 rounded-full"></div> Rủi ro cao
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PreviewTable;