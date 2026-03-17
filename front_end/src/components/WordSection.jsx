// src/components/WordSection.jsx
import React, { useState } from "react";
import api from "../constants/api_service"; // Luôn nhớ đường dẫn này
import axios from "axios";
import { FileText, Play, Download, Loader2 } from "lucide-react";

const WordSection = () => {
  const [file, setFile] = useState(null);
  const [report, setReport] = useState([]);
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

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
      <div className="border-2 border-dashed border-gray-200 rounded-2xl p-10 bg-gray-50/50 flex flex-col items-center justify-center">
        <input
          type="file"
          accept=".docx"
          onChange={(e) => setFile(e.target.files[0])}
          className="mb-4 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        <button
          onClick={handleStart}
          disabled={isProcessing || !file}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg disabled:bg-gray-300"
        >
          {isProcessing ? (
            <Loader2 className="animate-spin" />
          ) : (
            <Play size={18} />
          )}
          {isProcessing
            ? `Đang xử lý (${progress}%)`
            : "Bắt đầu thẩm định hàng loạt"}
        </button>
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
