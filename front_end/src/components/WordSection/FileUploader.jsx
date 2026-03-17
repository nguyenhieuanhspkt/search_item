import React from "react";
import { FileText, X, Play, Loader2 } from "lucide-react";

const FileUploader = ({
  file,
  onFileChange,
  onRemove,
  onStart,
  isProcessing,
  progress,
  loadingPreview,
}) => {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
      {!file ? (
        <div className="border-2 border-dashed border-gray-200 rounded-xl p-10 flex flex-col items-center hover:bg-gray-50 transition-all cursor-pointer relative">
          <input
            type="file"
            accept=".docx"
            onChange={onFileChange}
            className="absolute inset-0 opacity-0 cursor-pointer"
          />
          <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mb-3">
            <FileText className="text-blue-500" />
          </div>
          <p className="text-sm font-medium text-gray-700">
            Nhấn để tải lên file danh mục (.docx)
          </p>
        </div>
      ) : (
        <div className="flex items-center justify-between bg-blue-50/50 p-4 rounded-xl border border-blue-100">
          <div className="flex items-center gap-3">
            <div className="bg-white p-2 rounded-lg shadow-sm text-blue-600">
              <FileText size={20} />
            </div>
            <div>
              <p className="text-sm font-bold text-gray-800 truncate max-w-[200px]">
                {file.name}
              </p>
              <p className="text-xs text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onStart}
              disabled={isProcessing || loadingPreview}
              className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg text-sm font-bold flex items-center gap-2 shadow-md disabled:bg-gray-300 transition-all"
            >
              {isProcessing ? (
                <Loader2 className="animate-spin" size={16} />
              ) : (
                <Play size={16} fill="currentColor" />
              )}
              {isProcessing ? `Đang chạy ${progress}%` : "Bắt đầu thẩm định"}
            </button>
            <button
              onClick={onRemove}
              disabled={isProcessing}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploader;
