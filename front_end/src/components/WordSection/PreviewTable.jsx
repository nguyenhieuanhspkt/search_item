import React from "react";
import { Eye } from "lucide-react";

const PreviewTable = ({ data, isResult, loading }) => {
  if (!loading && data.length === 0) return null;

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden animate-in fade-in slide-in-from-top-2 duration-500">
      <div className="px-6 py-4 border-b border-gray-50 bg-gray-50/30 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Eye size={18} className="text-gray-400" />
          <span className="font-bold text-gray-700 text-sm">
            {isResult ? "Kết quả thẩm định" : "Xem trước dữ liệu bảng"}
          </span>
        </div>
        {loading && (
          <div className="text-xs text-blue-600 animate-pulse font-medium">
            Đang trích xuất dữ liệu...
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 text-gray-500 uppercase text-[10px] tracking-widest">
              <th className="px-6 py-3 font-semibold w-16 text-center">STT</th>
              <th className="px-6 py-3 font-semibold">Tên vật tư (Word)</th>
              <th className="px-6 py-3 font-semibold">Thông số kỹ thuật</th>
              <th className="px-6 py-3 font-semibold">Đơn vị tính</th>

              {isResult && (
                <>
                  <th className="px-6 py-3 font-semibold bg-blue-50/50 text-blue-600">
                    Gợi ý hệ thống
                  </th>
                  <th className="px-6 py-3 font-semibold bg-blue-50/50 text-blue-600">
                    Mã ERP
                  </th>
                  <th className="px-6 py-3 font-semibold bg-blue-50/50 text-blue-600 text-center">
                    Độ tin cậy
                  </th>
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {data.map((item, idx) => (
              <tr key={idx} className="hover:bg-gray-50/30 transition-colors">
                <td className="px-6 py-4 text-gray-400 font-mono text-center">
                  {item.stt}
                </td>
                <td className="px-6 py-4 font-medium text-gray-800">
                  {item.ten || item.tenWord}
                </td>
                <td className="px-6 py-4 text-gray-500">{item.ts}</td>
                <td className="px-6 py-4 text-gray-500">{item.dvt_word}</td>

                {isResult && (
                  <>
                    <td className="px-6 py-4 text-blue-700 font-medium">
                      {item.matchHeThong}
                    </td>
                    <td className="px-6 py-4">
                      <code className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs">
                        {item.erp}
                      </code>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`px-2 py-1 rounded-full text-[11px] font-bold ${
                          item.score >= 80
                            ? "bg-green-100 text-green-700"
                            : "bg-orange-100 text-orange-700"
                        }`}
                      >
                        {item.score}%
                      </span>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PreviewTable;
