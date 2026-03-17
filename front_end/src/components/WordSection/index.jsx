import React, { useState } from "react";
import axios from "axios";
import api from "../../constants/api_service";
import FileUploader from "./FileUploader";
import PreviewTable from "./PreviewTable";

const WordSection = () => {
  const [file, setFile] = useState(null);
  const [previewData, setPreviewData] = useState([]); // Chứa dữ liệu thô từ Word
  const [report, setReport] = useState([]); // Chứa dữ liệu đã thẩm định
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);

  // HÀM QUAN TRỌNG: Tự động chạy khi chọn file
  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setLoadingPreview(true); // Bật trạng thái đang đọc file
    setReport([]); // Xóa kết quả cũ
    setPreviewData([]); // Xóa preview cũ

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      // Gọi lên Python để trích xuất bảng
      const response = await axios.post(
        "http://10.156.43.63:8000/extract-word",
        formData,
      );

      // Đổ dữ liệu vào PreviewData để bảng hiện lên ngay
      setPreviewData(response.data);
    } catch (err) {
      alert("Lỗi trích xuất bảng: " + err.message);
      setFile(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleStart = async () => {
    if (previewData.length === 0) return;
    setIsProcessing(true);
    let tempResults = [];

    // Duyệt qua dữ liệu đang hiển thị ở Preview để thẩm định
    for (let i = 0; i < previewData.length; i++) {
      const item = previewData[i];
      try {
        const res = await api.searchQuery(`${item.ten} ${item.ts}`);
        const best = Array.isArray(res) ? res[0] : {};

        tempResults.push({
          ...item,
          tenWord: item.ten,
          matchHeThong: best.ten || "❌ Không thấy",
          erp: best.erp || "---",
          score: best.final_score || 0,
        });

        setReport([...tempResults]); // Cập nhật bảng kết quả theo thời gian thực
        setProgress(Math.round(((i + 1) / previewData.length) * 100));
      } catch (err) {
        console.error("Lỗi dòng " + i, err);
      }
    }
    setIsProcessing(false);
  };

  const handleRemove = () => {
    setFile(null);
    setPreviewData([]);
    setReport([]);
    setProgress(0);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">
        Thẩm định danh mục Word
      </h2>

      <FileUploader
        file={file}
        onFileChange={handleFileChange}
        onRemove={handleRemove}
        onStart={handleStart}
        isProcessing={isProcessing}
        progress={progress}
        loadingPreview={loadingPreview}
      />

      {/* BẢNG NÀY SẼ HIỆN KHI:
        1. Đang load preview (hiện skeleton/loading)
        2. Đã có previewData (hiện dữ liệu thô)
        3. Đã có report (hiện kết quả AI)
      */}
      <PreviewTable
        data={report.length > 0 ? report : previewData}
        isResult={report.length > 0}
        loading={loadingPreview}
      />
    </div>
  );
};

export default WordSection;
