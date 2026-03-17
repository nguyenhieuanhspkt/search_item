// src/components/WordSection.jsx
import { X } from "lucide-react"; // Import thêm icon X
import React, { useState } from "react";
import api from "../constants/api_service"; // Luôn nhớ đường dẫn này
import axios from "axios";
import { FileText, Play, Download, Loader2 } from "lucide-react";

const WordSection = () => {
  const [file, setFile] = useState(null);
  const [report, setReport] = useState([]);
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  // Hàm xóa file đã chọn
  const removeFile = () => {
    setFile(null);
    setReport([]); // Tùy chọn: Xóa báo cáo cũ nếu muốn
    setProgress(0);
  };
  const handleStart = async () => {
    if (!file) return alert("Vui lòng chọn file .docx!");

    setIsProcessing(true);
    setReport([]);
    setProgress(5); // Bắt đầu chạy nhẹ

    try {
      // 1. Gửi file lên server để lấy dữ liệu bảng (Endpoint bạn đã viết ở Backend)
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(
        "http://10.156.43.63:8000/extract-word",
        formData,
      );
      const rows = response.data;

      if (rows.length === 0) {
        alert("Không tìm thấy bảng dữ liệu hợp lệ!");
        setIsProcessing(false);
        return;
      }

      // 2. Chạy vòng lặp thẩm định từng dòng
      let tempResults = [];
      for (let i = 0; i < rows.length; i++) {
        const item = rows[i];
        const res = await api.searchQuery(`${item.ten} ${item.ts}`);

        const bestMatch = Array.isArray(res) ? res[0] : {};

        tempResults.push({
          stt: item.stt,
          tenWord: item.ten,
          matchHeThong: bestMatch.ten || "❌ Không tìm thấy",
          erp: bestMatch.erp || "---",
          score: bestMatch.final_score || 0,
        });

        // Cập nhật UI ngay lập tức cho từng dòng (Realtime)
        setReport([...tempResults]);
        setProgress(Math.round(((i + 1) / rows.length) * 100));
      }
    } catch (error) {
      alert("Lỗi quá trình thẩm định: " + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-4">
        <FileText className="text-blue-600" size={32} />
        <h2 className="text-2xl font-bold text-gray-800">
          Thẩm định danh mục từ file Word
        </h2>
      </div>

      {/* Dropzone Area */}
      <div className="border-2 border-dashed border-gray-200 rounded-2xl p-10 bg-gray-50/50 flex flex-col items-center justify-center transition-all">
        {!file ? (
          // TRƯỜNG HỢP 1: CHƯA CHỌN FILE
          <div className="flex flex-col items-center">
            <input
              type="file"
              id="file-upload"
              accept=".docx"
              onChange={(e) => setFile(e.target.files[0])}
              className="hidden" // Ẩn input mặc định xấu xí
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer bg-blue-50 text-blue-700 px-6 py-2 rounded-full font-semibold hover:bg-blue-100 transition-colors"
            >
              Chọn tệp Word (.docx)
            </label>
            <p className="mt-2 text-gray-400 text-sm">
              Kéo thả hoặc click để chọn file
            </p>
          </div>
        ) : (
          // TRƯỜNG HỢP 2: ĐÃ CHỌN FILE -> HIỆN TÊN VÀ NÚT XÓA
          <div className="w-full max-w-md">
            <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-blue-100 shadow-sm mb-6">
              <div className="flex items-center gap-3 overflow-hidden">
                <FileText className="text-blue-500 flex-shrink-0" size={24} />
                <span className="text-sm font-medium text-gray-700 truncate">
                  {file.name}
                </span>
              </div>

              <button
                onClick={removeFile}
                disabled={isProcessing} // Không cho xóa khi đang chạy AI
                className="p-1 hover:bg-red-50 text-gray-400 hover:text-red-500 rounded-full transition-colors disabled:opacity-30"
                title="Xóa file"
              >
                <X size={20} />
              </button>
            </div>

            <button
              onClick={handleStart}
              disabled={isProcessing}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg disabled:bg-gray-300"
            >
              {isProcessing ? (
                <Loader2 className="animate-spin" />
              ) : (
                <Play size={18} fill="currentColor" />
              )}
              {isProcessing
                ? `Đang xử lý (${progress}%)`
                : "Bắt đầu thẩm định hàng loạt"}
            </button>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {isProcessing && (
        <div className="w-full bg-gray-100 h-3 rounded-full overflow-hidden border border-gray-200">
          <div
            className="bg-green-500 h-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      )}

      {/* Table Results */}
      {report.length > 0 && (
        <div className="mt-8 overflow-hidden rounded-xl border border-gray-100 shadow-sm">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 border-b border-gray-100 text-gray-600">
              <tr>
                <th className="px-4 py-3 font-semibold">STT</th>
                <th className="px-4 py-3 font-semibold">Vật tư (Word)</th>
                <th className="px-4 py-3 font-semibold">Kết quả khớp nhất</th>
                <th className="px-4 py-3 font-semibold">ERP</th>
                <th className="px-4 py-3 font-semibold">Độ tin cậy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {report.map((item, idx) => (
                <tr key={idx} className="hover:bg-blue-50/30 transition-colors">
                  <td className="px-4 py-3 text-gray-500">{item.stt}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">
                    {item.tenWord}
                  </td>
                  <td className="px-4 py-3 text-blue-700">
                    {item.matchHeThong}
                  </td>
                  <td className="px-4 py-3">
                    <code className="text-xs bg-gray-100 px-1 rounded">
                      {item.erp}
                    </code>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`font-bold ${item.score > 80 ? "text-green-600" : "text-orange-500"}`}
                    >
                      {item.score}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default WordSection;
