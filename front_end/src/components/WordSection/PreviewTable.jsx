import React from "react";
import { 
  Eye, CheckCircle2, AlertTriangle, XCircle, 
  DollarSign, Box, Calendar, FileText, Info 
} from "lucide-react";

const PreviewTable = ({ data, isResult, loading }) => {
  if (!loading && (!data || data.length === 0)) return null;

  // 1. Hàm render điểm số kèm màu sắc
  const renderScore = (score) => {
    if (!score && score !== 0) return <span className="text-gray-400">0%</span>;
    const s = score > 1 ? score : score * 100;
    const value = s.toFixed(1);
    let colorClass = "text-red-500";
    if (s >= 80) colorClass = "text-green-600 font-black";
    else if (s >= 50) colorClass = "text-orange-500 font-bold";
    return <span className={colorClass}>{value}%</span>;
  };

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden animate-in fade-in slide-in-from-top-2 duration-500">
      {/* Header Bảng */}
      <div className="px-6 py-4 border-b border-gray-50 bg-gray-50/30 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Eye size={18} className="text-gray-400" />
          <span className="font-bold text-gray-700 text-sm">
            {isResult ? "Báo cáo Thẩm định Chi tiết (AI + Core2 Metadata)" : "Xem trước dữ liệu Word"}
          </span>
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-xs text-blue-600 animate-pulse font-medium">
            <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
            Đang truy vấn dữ liệu kho...
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-separate border-spacing-0">
          <thead>
            <tr className="bg-gray-50 text-gray-600 text-[10px] uppercase tracking-wider font-black">
              <th className="p-4 text-center w-12 border-b border-gray-100">STT</th>
              <th className="p-4 text-left border-b border-gray-100 w-[250px]">Vật tư (Word)</th>
              <th className="p-4 text-left border-b border-gray-100">Kết quả đối chiếu hệ thống (VT4)</th>
              <th className="p-4 text-center border-b border-gray-100">Thông tin kho & Giá</th>
              <th className="p-4 text-center border-b border-gray-100">Mã ERP</th>
              <th className="p-4 text-center border-b border-gray-100">Tin cậy</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-100">
            {data.map((item, idx) => (
              <tr key={idx} className="hover:bg-blue-50/30 transition-all group align-top">
                {/* Cột 1: STT */}
                <td className="p-4 text-center text-[10px] text-gray-400 font-bold">
                  {item.stt || idx + 1}
                </td>
                
                {/* Cột 2: Dữ liệu gốc từ Word */}
                <td className="p-4">
                  <div className="text-sm font-bold text-slate-800 leading-snug whitespace-pre-line">
                    {item.ten}
                  </div>
                  <div className="text-[10px] text-orange-600 mt-2 font-bold uppercase tracking-tighter">
                    ĐVT Word: {item.dvt_word || item.dvt || "N/A"}
                  </div>
                </td>

                {/* Cột 3: Tên khớp + Highlight + Trọng số AI */}
                <td className="p-4">
                  <div 
                    className="text-sm font-medium leading-relaxed text-blue-900 mb-2"
                    dangerouslySetInnerHTML={{ __html: item.diff_html || item.matchHeThong || "---" }} 
                  />
                  
                  {/* Badge trọng số AI (Giống bên search đơn lẻ) */}
                  {item.explain && typeof item.explain === 'object' && !item.explain.isMeili && (
                    <div className="flex flex-wrap gap-1 mt-2">
                       <span className="text-[8px] bg-slate-100 px-1 py-0.5 rounded text-gray-500">C:{item.explain.weighted_cross}</span>
                       <span className="text-[8px] bg-slate-100 px-1 py-0.5 rounded text-gray-500">B:{item.explain.weighted_bi}</span>
                       <span className="text-[8px] bg-green-100 px-1 py-0.5 rounded text-green-700 font-bold">+{item.explain.bonus}</span>
                    </div>
                  )}
                  {item.engine && <div className="text-[9px] text-gray-400 mt-1 italic uppercase">Nguồn: {item.engine}</div>}
                </td>

                {/* Cột 4: Metadata (Giá, Kho, HĐ) - ĐÂY LÀ PHẦN HIẾU MUỐN THÊM */}
                <td className="p-4">
                  <div className="flex flex-col gap-2 min-w-[150px]">
                    <div className="flex items-center gap-2 bg-green-50 px-2 py-1 rounded-lg border border-green-100">
                      <DollarSign size={12} className="text-green-600" />
                      <span className="text-[11px] font-black text-green-700">
                        {item.don_gia ? `${item.don_gia.toLocaleString()}đ` : "---"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 bg-purple-50 px-2 py-1 rounded-lg border border-purple-100">
                      <Box size={12} className="text-purple-600" />
                      <span className="text-[10px] font-bold text-purple-700 truncate" title={item.kho}>
                        {item.kho?.split('-')[0] || "---"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 bg-slate-50 px-2 py-1 rounded-lg border border-slate-100">
                      <FileText size={12} className="text-slate-500" />
                      <span className="text-[9px] font-medium text-slate-600 truncate w-24" title={item.hop_dong}>
                        {item.hop_dong || "Chưa có HĐ"}
                      </span>
                    </div>
                  </div>
                </td>

                {/* Cột 5: Mã ERP */}
                <td className="p-4 text-center">
                  <div className="flex flex-col items-center gap-1">
                    <code className="bg-slate-900 text-slate-100 px-2 py-1 rounded font-mono text-[11px] font-bold">
                      {item.erp || "---"}
                    </code>
                    <span className="text-[10px] text-blue-700 font-black">{item.dvt || "Cái"}</span>
                  </div>
                </td>

                {/* Cột 6: Score */}
                <td className="p-4 text-center">
                  <div className="flex flex-col items-center">
                    {renderScore(item.score)}
                    {item.explain?.why && (
                      <div className="text-[8px] text-gray-400 mt-1 uppercase tracking-tighter w-16 leading-tight">
                        {item.explain.why[0]}
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* FOOTER */}
      {isResult && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 flex justify-between items-center">
          <p className="text-[10px] text-gray-400 font-bold italic">
            * Hệ thống đã đồng bộ Metadata từ Core2 (Meilisearch) cho kết quả AI.
          </p>
          <div className="flex gap-4">
             <div className="flex items-center gap-1 text-[10px] font-bold text-green-600"><CheckCircle2 size={12}/> Khớp</div>
             <div className="flex items-center gap-1 text-[10px] font-bold text-orange-500"><AlertTriangle size={12}/> Soi lại</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PreviewTable;