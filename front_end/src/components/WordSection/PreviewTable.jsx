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
            <tr className="bg-gray-50 text-gray-500 uppercase text-[10px] tracking-widest">
              <th className="px-6 py-4 font-semibold w-16 text-center border-r border-gray-100">STT</th>
              <th className="px-6 py-4 font-semibold min-w-[220px]">Nội dung gốc (Word)</th>
              
              {isResult ? (
                <>
                  <th className="px-6 py-4 font-semibold bg-blue-50/40 text-blue-600 min-w-[280px]">
                    Gợi ý hệ thống & Chủng loại
                  </th>
                  <th className="px-6 py-4 font-semibold bg-blue-50/40 text-blue-600">ĐVT Hệ thống</th>
                  <th className="px-6 py-4 font-semibold bg-blue-50/40 text-blue-600 text-center">Độ tin cậy</th>
                </>
              ) : (
                <>
                  <th className="px-6 py-4 font-semibold">Thông số kỹ thuật</th>
                  <th className="px-6 py-4 font-semibold">ĐVT (Word)</th>
                </>
              )}
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-50">
            {data.map((item, idx) => (
              <tr key={idx} className="hover:bg-gray-50/40 transition-colors group">
                <td className="px-6 py-4 text-gray-400 font-mono text-center text-xs border-r border-gray-50">
                  {item.stt || idx + 1}
                </td>
                
                {/* Phần Nội dung gốc từ Word */}
                <td className="px-6 py-4">
                  <div className="font-medium text-gray-800 leading-snug">
                    {item.ten || item.tenWord}
                  </div>
                  <div className="text-[11px] text-gray-400 mt-1 italic line-clamp-1">
                    {item.ts || "Không có thông số"}
                  </div>
                </td>

                {!isResult && (
                  <>
                    <td className="px-6 py-4 text-gray-500 text-xs">{item.ts || "---"}</td>
                    <td className="px-6 py-4 text-gray-500 text-xs font-medium">{item.dvt_word || "---"}</td>
                  </>
                )}

                {/* Phần Kết quả AI trả về */}
                {isResult && (
                  <>
                    <td className="px-6 py-4">
                      <div className="text-blue-900 font-bold text-sm mb-2">
                        {item.matchHeThong}
                      </div>
                      
                      <div className="flex flex-wrap gap-2">
                        {/* Tag Mã ERP */}
                        <span className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-100 text-[10px] font-mono font-bold">
                          <Box size={10} /> {item.erp}
                        </span>
                        
                        {/* Tag Chủng loại tự động */}
                        {item.chung_loai && (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-semibold transition-all ${getCategoryStyle(item.chung_loai)}`}>
                            <Tag size={10} /> {item.chung_loai}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Cột Đơn vị tính và cảnh báo lệch ĐVT */}
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <span className="text-gray-700 font-bold">{item.dvt || "N/A"}</span>
                        {item.dvt_word && item.dvt_word.toLowerCase() !== (item.dvt || "").toLowerCase() && (
                          <span className="text-[9px] text-red-500 flex items-center gap-0.5 mt-1 font-medium bg-red-50 px-1 rounded">
                            <AlertCircle size={8} /> Lệch gốc: {item.dvt_word}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Cột Điểm số % */}
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center gap-1">
                        <span className={`min-w-[45px] py-1 rounded-lg text-[11px] font-black shadow-sm border ${
                          item.score >= 80 
                            ? "bg-green-500 text-white border-green-600" 
                            : item.score >= 55 
                            ? "bg-amber-400 text-white border-amber-500" 
                            : "bg-rose-500 text-white border-rose-600"
                        }`}>
                          {item.score}%
                        </span>
                        {item.score < 60 && (
                          <span className="text-[9px] text-rose-600 font-bold uppercase tracking-tighter">Cần soát lại</span>
                        )}
                      </div>
                    </td>
                  </>
                )}
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