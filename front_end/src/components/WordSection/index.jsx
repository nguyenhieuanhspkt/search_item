import React, { useState } from "react";
import api from "../../constants/api_service";
import FileUploader from "./FileUploader";
import PreviewTable from "./PreviewTable";

const WordSection = () => {
  // --- Các State quản lý dữ liệu ---
  const [file, setFile] = useState(null);
  const [previewData, setPreviewData] = useState([]); // Dữ liệu thô trích xuất từ Word
  const [report, setReport] = useState([]); // Dữ liệu sau khi AI thẩm định
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);

  /**
   * Bước 1: Xử lý khi chọn file - Hiển thị Preview ngay lập tức
   */
  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    // Kiểm tra định dạng file
    if (!selectedFile.name.endsWith(".docx")) {
      alert("Vui lòng chọn file định dạng .docx");
      return;
    }

    setFile(selectedFile);
    setLoadingPreview(true);
    setReport([]); // Reset kết quả cũ
    setPreviewData([]); // Reset preview cũ

    try {
      // Gọi API trích xuất bảng thông qua api_service
      const data = await api.extractWord(selectedFile);

      if (data && data.length > 0) {
        setPreviewData(data);
      } else {
        alert("Không tìm thấy bảng dữ liệu hợp lệ trong file Word!");
        setFile(null);
      }
    } catch (err) {
      console.error("Lỗi trích xuất:", err);
      alert("Lỗi kết nối server hoặc file không đúng định dạng bảng.");
      setFile(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  /**
   * Bước 2: Chạy thẩm định AI cho từng dòng dữ liệu trong Preview
   */
  const handleStart = async () => {
    if (previewData.length === 0) return;

    setIsProcessing(true);
    setProgress(0);
    let tempResults = [];

    // Duyệt qua từng dòng dữ liệu đang hiện ở Preview
    for (let i = 0; i < previewData.length; i++) {
      const item = previewData[i];
      try {
        // Query kết hợp Tên và Thông số để AI tìm kiếm chính xác nhất
        const queryText = `${item.ten} ${item.ts}`;
        const searchRes = await api.searchQuery(queryText);

        // Lấy kết quả tốt nhất từ danh sách trả về
        const bestMatch = Array.isArray(searchRes) ? searchRes[0] : {};

        tempResults.push({
          ...item, // Giữ lại STT, Tên gốc, Thông số gốc
          tenWord: item.ten, // Lưu lại tên gốc để hiển thị
          matchHeThong: bestMatch.ten || "❌ Không tìm thấy",
          erp: bestMatch.erp || "---",
          score: bestMatch.final_score || 0,
        });

        // Cập nhật bảng kết quả (Report) theo thời gian thực (Real-time)
        setReport([...tempResults]);

        // Tính toán % tiến độ
        const currentProgress = Math.round(
          ((i + 1) / previewData.length) * 100,
        );
        setProgress(currentProgress);
      } catch (err) {
        console.error(`Lỗi thẩm định dòng ${i + 1}:`, err);
      }
    }
    setIsProcessing(false);
  };

  /**
   * Bước 3: Xóa file và dọn dẹp dữ liệu
   */
  const handleRemove = () => {
    if (isProcessing) {
      if (!window.confirm("Hệ thống đang xử lý, bạn có chắc chắn muốn hủy?"))
        return;
    }
    setFile(null);
    setPreviewData([]);
    setReport([]);
    setProgress(0);
    setIsProcessing(false);
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Tiêu đề phần chức năng */}
      <div className="border-b border-gray-100 pb-4">
        <h2 className="text-2xl font-bold text-gray-800">
          Thẩm định danh mục từ file Word
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Hệ thống sẽ tự động trích xuất bảng dữ liệu và đối chiếu với danh mục
          ERP của nhà máy.
        </p>
      </div>

      {/* Component điều khiển việc tải file và các nút lệnh */}
      <FileUploader
        file={file}
        onFileChange={handleFileChange}
        onRemove={handleRemove}
        onStart={handleStart}
        isProcessing={isProcessing}
        progress={progress}
        loadingPreview={loadingPreview}
      />

      {/* Component hiển thị bảng (Tự động chuyển đổi Preview -> Result) */}
      <PreviewTable
        data={report.length > 0 ? report : previewData}
        isResult={report.length > 0}
        loading={loadingPreview}
      />

      {/* Ghi chú chân trang nếu cần */}
      {report.length > 0 && !isProcessing && (
        <div className="text-center text-xs text-gray-400 italic mt-4">
          * Kết quả dựa trên thuật toán so khớp Hybrid Search. Vui lòng kiểm tra
          lại các dòng có độ tin cậy thấp.
        </div>
      )}
    </div>
  );
};

export default WordSection;
