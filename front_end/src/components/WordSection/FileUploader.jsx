import React from "react";
// Hiếu lưu ý: Đã thêm UploadCloud và các icon cần thiết vào đây
import { FileText, X, Play, Loader2, UploadCloud, CheckCircle } from "lucide-react";

const FileUploader = ({ onFileChange, onRemove, onStart, file, isProcessing, loadingPreview, progress }) => {
  return (
    <div className="bg-slate-50 border-2 border-dashed border-slate-200 rounded-[32px] p-10 text-center transition-all relative overflow-hidden">
      
      {/* Hiệu ứng Progress Bar chạy ngầm nếu đang xử lý */}
      {isProcessing && (
        <div 
          className="absolute bottom-0 left-0 h-1.5 bg-blue-600 transition-all duration-500" 
          style={{ width: `${progress}%` }}
        />
      )}

      <div className="max-w-md mx-auto">
        {/* Icon chính */}
        <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg transition-all ${
          file ? "bg-emerald-500 shadow-emerald-100" : "bg-blue-600 shadow-blue-100"
        }`}>
          {loadingPreview ? (
            <Loader2 className="text-white animate-spin" size={32} />
          ) : file ? (
            <CheckCircle className="text-white" size={32} />
          ) : (
            <UploadCloud className="text-white" size={32} />
          )}
        </div>
        
        <h3 className="text-xl font-bold text-slate-800 mb-2">
          {file ? "File đã sẵn sàng" : "Tải lên danh mục vật tư"}
        </h3>
        
        <p className="text-sm text-slate-500 mb-6 font-medium">
          Hỗ trợ file <span className="text-blue-600 font-bold">.docx</span> hoặc <span className="text-emerald-600 font-bold">.xlsx</span>
          <br/>Cấu trúc chuẩn: <span className="text-slate-700 font-bold">STT | Tên | Thông số | ĐVT</span>
        </p>

        <div className="flex flex-col gap-3 items-center justify-center">
          {!file ? (
            /* NÚT CHỌN FILE (Khi chưa có file) */
            <label className={`
              inline-flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-wider transition-all cursor-pointer
              ${loadingPreview || isProcessing 
                ? "bg-slate-200 text-slate-400 cursor-not-allowed" 
                : "bg-slate-900 text-white hover:bg-blue-600 shadow-xl shadow-slate-200 active:scale-95"}
            `}>
              <FileText size={18} />
              Nhấn để chọn file
              <input 
                type="file" 
                className="hidden" 
                accept=".docx,.xlsx,.xls" 
                onChange={onFileChange}
                disabled={loadingPreview || isProcessing}
              />
            </label>
          ) : (
            /* NHÓM NÚT ĐIỀU KHIỂN (Khi đã có file) */
            <div className="flex flex-wrap gap-3 justify-center">
              {/* Nút Chạy Thẩm Định */}
              <button
                onClick={onStart}
                disabled={isProcessing || loadingPreview}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl shadow-blue-100 transition-all disabled:bg-slate-300 active:scale-95"
              >
                {isProcessing ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Đang thẩm định {Math.round(progress)}%
                  </>
                ) : (
                  <>
                    <Play size={18} fill="currentColor" />
                    Bắt đầu thẩm định
                  </>
                )}
              </button>

              {/* Nút Hủy/Xóa file */}
              <button
                onClick={onRemove}
                disabled={isProcessing}
                className="flex items-center gap-2 bg-white border-2 border-slate-200 text-slate-600 hover:bg-red-50 hover:text-red-600 hover:border-red-100 px-6 py-4 rounded-2xl font-black text-sm uppercase tracking-widest transition-all disabled:opacity-50"
              >
                <X size={18} />
                Hủy
              </button>
            </div>
          )}
        </div>

        {file && (
          <div className="mt-6 p-3 bg-white border border-slate-100 rounded-xl inline-block">
             <span className="text-[10px] font-black text-slate-400 uppercase mr-2">Đang chọn:</span>
             <span className="text-xs font-bold text-blue-600">{file.name}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUploader;