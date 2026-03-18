import React, { useState } from "react";
import * as XLSX from 'xlsx';
import { Download, FileCheck } from 'lucide-react';
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

    if (!selectedFile.name.endsWith(".docx")) {
      alert("Vui lòng chọn file định dạng .docx");
      return;
    }

    setFile(selectedFile);
    setLoadingPreview(true);
    setReport([]); 
    setPreviewData([]); 

    try {
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
   * Bước 2: Chạy thẩm định AI hàng loạt (Bulk Match)
   */
  const handleStart = async () => {
    if (previewData.length === 0) return;
    
    setIsProcessing(true);
    setProgress(20); // Bắt đầu gửi dữ liệu đi

    try {
      // Chuẩn bị payload khớp với MaterialInput ở Backend
      const payload = previewData.map(item => ({
        stt: item.stt || "",
        ten: item.ten,
        tskt: item.ts || "", 
        dvt: item.dvt_word || ""
      }));

      const res = await api.bulkMatch(payload);

      if (res.status === "success") {
        // Map lại kết quả từ Backend trả về
        const formattedResults = res.data.map((item, index) => ({
          ...previewData[index],
          tenWord: previewData[index].ten, // Giữ lại tên gốc để xuất Excel
          matchHeThong: item.stock_name || item.ten_vattu,
          erp: item.erp || item.ma_vattu,
          dvt: item.dvt_he_thong || item.dvt, // Hứng ĐVT
          chung_loai: item.chung_loai, // Hứng Chủng loại
          score: item.score
        }));
        
        setReport(formattedResults);
        setProgress(100);
      } else {
        alert("Lỗi thẩm định: " + res.message);
      }
    } catch (err) {
      console.error("Lỗi Bulk Match:", err);
      alert("Không thể kết nối với AI Server để thẩm định hàng loạt!");
    } finally {
      setIsProcessing(false);
    }
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

  /**
   * Bước 4: Xuất file Excel kết quả thẩm định
   */
  const exportToExcel = () => {
    if (!report || report.length === 0) return;

    const dataForExcel = report.map((item, index) => ({
      "STT": item.stt || index + 1,
      "Tên vật tư (Word)": item.tenWord,
      "Thông số kỹ thuật (Word)": item.ts,
      "Vật tư khớp nhất (Hệ thống)": item.matchHeThong,
      "Mã vật tư (ERP)": item.erp,
      "Độ tin cậy (%)": (item.score > 1 ? item.score : item.score * 100).toFixed(1) + "%",
      "Ghi chú": item.score < 0.6 && item.score < 60 ? "Cần kiểm tra lại" : "Khớp"
    }));

    const worksheet = XLSX.utils.json_to_sheet(dataForExcel);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "KetQuaThamDinh");

    // Tạo tên file kèm timestamp để dễ quản lý tại cơ quan
    const timeStr = new Date().getTime();
    const fileName = `Ket_qua_tham_dinh_VT4_${timeStr}.xlsx`;
    XLSX.writeFile(workbook, fileName);
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex justify-between items-center border-b border-gray-100 pb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
             <FileCheck className="text-blue-600" /> Thẩm định file Word
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Hệ thống tự động trích xuất và đối chiếu danh mục ERP nhà máy.
          </p>
        </div>

        {/* Nút Xuất Excel */}
        {report.length > 0 && !isProcessing && (
          <button 
            onClick={exportToExcel}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-lg transition-all"
          >
            <Download size={18} />
            Xuất Báo cáo
          </button>
        )}
      </div>

      <FileUploader
        file={file}
        onFileChange={handleFileChange}
        onRemove={handleRemove}
        onStart={handleStart}
        isProcessing={isProcessing}
        progress={progress}
        loadingPreview={loadingPreview}
      />

      <PreviewTable
        data={report.length > 0 ? report : previewData}
        isResult={report.length > 0}
        loading={loadingPreview}
      />

      {report.length > 0 && !isProcessing && (
        <div className="text-center text-[10px] text-gray-400 italic mt-4">
          * Kết quả dựa trên thuật toán so khớp Hybrid Search (BGE-M3). 
          Vui lòng kiểm tra lại các dòng có độ tin cậy thấp.
        </div>
      )}
    </div>
  );
};

export default WordSection;