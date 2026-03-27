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

    const fileName = selectedFile.name.toLowerCase();
    setFile(selectedFile);
    setLoadingPreview(true);
    setReport([]); 
    setPreviewData([]); 

    try {
      if (fileName.endsWith(".xlsx") || fileName.endsWith(".xls")) {
        const data = await selectedFile.arrayBuffer();
        const workbook = XLSX.read(data, { type: 'array' });
        const worksheet = workbook.Sheets[workbook.SheetNames[0]];
        
        // Đọc dữ liệu thô
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        
        if (jsonData.length > 0) {
          // KIỂM TRA SỐ CỘT CỦA HÀNG ĐẦU TIÊN (HEADER)
          // Nếu số cột > 4, chặn luôn không cho lấy dữ liệu
          const columnCount = jsonData[0].length;
          
          if (columnCount > 4) {
            alert(`File Excel có ${columnCount} cột. Hệ thống yêu cầu ĐÚNG 4 cột: STT | Tên | Thông số | ĐVT. Vui lòng chỉnh lại file!`);
            setFile(null);
            setLoadingPreview(false);
            return; // Dừng lại ở đây
          }

          const formatted = jsonData
            .slice(1) // Bỏ hàng tiêu đề
            .filter(row => row[1]) // Bắt buộc phải có Tên vật tư
            .map(row => ({
              stt: String(row[0] || ""),
              ten: String(row[1] || ""),
              ts: String(row[2] || ""),
              dvt_word: String(row[3] || "")
            }));

          setPreviewData(formatted);
        }
      } 
      else if (fileName.endsWith(".docx")) {
        // Logic Word giữ nguyên...
        const data = await api.extractWord(selectedFile);
        if (data && !data.error) setPreviewData(data);
      }
    } catch (err) {
      alert("Lỗi xử lý file!");
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
  setProgress(0);
  setReport([]);

  try {
    const payload = previewData.map(item => ({
      stt: String(item.stt || ""),
      ten: item.ten || "",
      tskt: item.ts || "",
      dvt: item.dvt_word || ""
    }));

    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/bulk-match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulated = [];

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const res = JSON.parse(line.replace('data: ', ''));
          if (res.status === "progress" && res.data) {
            // --- BƯỚC QUAN TRỌNG: TRUY VẤN NGƯỢC MEILI CHO MỖI CHUNK ---
            const enrichedData = await Promise.all(res.data.map(async (aiItem) => {
              if (!aiItem.erp || aiItem.erp === "---") return aiItem;
              
              try {
                // Gọi Meili để lấy Metadata gốc
                const meiliRes = await api.searchMeilisearch(aiItem.erp);
                const meta = meiliRes?.hits?.[0]; 
                return {
                  ...aiItem,
                  // Đắp thêm metadata từ Meili vào kết quả AI
                  don_gia: meta?.["Đơn Giá Nhập"],
                  hop_dong: meta?.["Số Hợp Đồng/QĐ"],
                  kho: meta?.["Kho"],
                  nam: meta?.["Năm"],
                  matchHeThong: meta?.["Tên vật tư (NXT)"] || aiItem.matchHeThong
                };
              } catch (e) { return aiItem; }
            }));

            const newBatch = enrichedData.map((item, index) => ({
              ...previewData[accumulated.length + index],
              ...item,
              score: item.score > 1 ? item.score / 100 : item.score
            }));

            accumulated = [...accumulated, ...newBatch];
            setReport([...accumulated]);
            setProgress(res.percent);
          }
        }
      }
    }
  } catch (err) {
    alert("Lỗi kết nối hệ thống!");
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

    const dataForExcel = report.map((item, index) => {
      // 1. Chuẩn hóa Score về dạng 0-100 để hiển thị
      const finalScore = item.score > 1 ? item.score : (item.score * 100);
      
      return {
        "STT": item.stt || index + 1,
        // --- Dữ liệu gốc từ Word ---
        "Tên vật tư (Word)": item.ten || "",
        "Thông số (Word)": item.ts || "",
        "ĐVT (Word)": item.dvt_word || "",

        // --- Kết quả đối chiếu từ Hệ thống ---
        "Mã ERP": item.erp || "---",
        "Vật tư khớp nhất (VT4)": item.matchHeThong || "Không tìm thấy",
        "ĐVT Hệ thống": item.dvt || "",
        "Nguồn xử lý": item.engine || "AI Search", // BIẾN MỚI: Biết món nào khớp mã, món nào AI tìm

        // --- Đánh giá AI ---
        "Độ tin cậy (%)": finalScore.toFixed(1) + "%",
        "Giải thích chi tiết": (item.explain && typeof item.explain === 'string') 
                               ? item.explain.replace(/<[^>]*>?/gm, '') // Xóa thẻ HTML nếu có
                               : "",
        
        // --- Ghi chú thẩm định ---
        "Kết luận": finalScore >= 80 ? "Khớp hoàn toàn" : (finalScore >= 50 ? "Cần kiểm tra lại" : "Lệch thông tin")
      };
    });

    const worksheet = XLSX.utils.json_to_sheet(dataForExcel);
    
    // Cập nhật độ rộng cột (Thêm 1 cột nên mảng này dài thêm 1 phần tử)
    const wscols = [
      { wch: 5 },  // STT
      { wch: 35 }, // Tên Word
      { wch: 30 }, // Thông số Word
      { wch: 10 }, // ĐVT Word
      { wch: 15 }, // ERP
      { wch: 40 }, // Vật tư hệ thống
      { wch: 12 }, // ĐVT Hệ thống
      { wch: 15 }, // Nguồn xử lý (Mới)
      { wch: 15 }, // Độ tin cậy
      { wch: 50 }, // Giải thích
      { wch: 20 }, // Kết luận
    ];
    worksheet['!cols'] = wscols;

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "KetQuaThamDinh");

    const timeStr = new Date().toLocaleDateString('vi-VN').replace(/\//g, '-');
    const fileName = `Bao_cao_Tham_dinh_Vinh_Tan_4_${timeStr}.xlsx`;
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