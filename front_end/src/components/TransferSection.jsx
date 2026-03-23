import React, { useState, useEffect } from "react";
import { UploadCloud, File, CheckCircle, AlertCircle, Loader2, History, HardDrive } from "lucide-react";
import api from "../constants/api_service";

const TransferSection = () => {
  const [files, setFiles] = useState([]);
  const [serverFiles, setServerFiles] = useState([]); // Danh sách file thực tế trong folder
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState({ type: "", text: "" });

  // Hàm lấy danh sách file hiện có trong folder từ Backend
  const fetchServerFiles = async () => {
    const data = await api.getUploadedFiles();
    setServerFiles(data);
  };

  // Load danh sách file khi vừa vào trang
  useEffect(() => {
    fetchServerFiles();
  }, []);

  const handleUpload = async () => {
    setUploading(true);
    setProgress(0);
    setMessage({ type: "", text: "" });

    try {
      const res = await api.uploadFiles(files, (p) => {
        setProgress(p);
      });
      
      setMessage({ type: "success", text: "Gửi file thành công! Hiếu đã nhận được." });
      setFiles([]);
      // Cập nhật lại danh sách file hiển thị phía dưới
      await fetchServerFiles(); 
    } catch (err) {
      setMessage({ type: "error", text: "Lỗi: " + (err.response?.data?.detail || err.message) });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 text-gray-800">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-blue-600 uppercase tracking-tight">Cổng Nhận Tài Liệu</h2>
        <p className="text-sm text-gray-500 mt-1 flex items-center justify-center gap-1">
          <HardDrive size={14} /> Thư mục: Thẩm định 98_hieuna_3
        </p>
      </div>

      {/* Box chọn file */}
      <div className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
        files.length > 0 ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-gray-50 hover:border-blue-400"
      }`}>
        <input type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files))} className="hidden" id="file-up" disabled={uploading} />
        <label htmlFor="file-up" className="cursor-pointer flex flex-col items-center">
          <UploadCloud size={48} className={`${uploading ? "animate-bounce text-gray-400" : "text-blue-500"} mb-3`} />
          <span className="font-semibold text-lg italic text-gray-700">Chọn tài liệu gửi cho Hiếu</span>
          <span className="text-[11px] text-gray-400 mt-1 underline">Hỗ trợ file nặng lên đến 1GB</span>
        </label>
      </div>

      {/* List file chuẩn bị upload */}
      {files.length > 0 && !uploading && (
        <div className="bg-white p-3 rounded-xl border border-blue-100 shadow-sm max-h-32 overflow-y-auto animate-in fade-in zoom-in duration-300">
          <p className="text-[10px] font-bold text-blue-500 mb-2 uppercase">File đã chọn ({files.length}):</p>
          {files.map((f, i) => (
            <div key={i} className="flex justify-between text-[11px] py-1 text-gray-600 font-mono border-b border-gray-50 last:border-0">
              <span className="truncate pr-2 italic flex items-center gap-1"><File size={12}/> {f.name}</span>
              <span className="shrink-0 text-blue-400">{(f.size / 1024 / 1024).toFixed(1)}MB</span>
            </div>
          ))}
        </div>
      )}

      {/* Progress Bar */}
      {uploading && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-bold text-blue-600 uppercase">
            <span>Đang truyền tệp tin...</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 h-3 rounded-full overflow-hidden shadow-inner">
            <div className="bg-blue-600 h-full transition-all duration-300 shadow-[0_0_12px_rgba(37,99,235,0.6)]" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      )}

      {/* Status Message */}
      {message.text && (
        <div className={`p-4 rounded-xl text-sm flex items-center gap-3 border animate-bounce-short ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'
        }`}>
          {message.type === 'success' ? <CheckCircle size={18}/> : <AlertCircle size={18}/>}
          <span className="font-medium">{message.text}</span>
        </div>
      )}

      <button onClick={handleUpload} disabled={uploading || !files.length} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-2xl font-bold shadow-lg transition-all active:scale-95 disabled:bg-gray-300 flex justify-center items-center gap-2">
        {uploading ? <><Loader2 className="animate-spin" size={20}/> ĐANG GỬI...</> : `XÁC NHẬN GỬI TÀI LIỆU`}
      </button>

      {/* --- PHẦN FEEDBACK: DANH SÁCH FILE HIỆN CÓ TRONG THƯ MỤC --- */}
      <div className="mt-8 pt-6 border-t border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-gray-500 font-bold text-xs uppercase tracking-wider">
            <History size={16} />
            <span>Tệp đã nhận trong folder của Hiếu</span>
          </div>
          <span className="text-[10px] bg-gray-100 px-2 py-0.5 rounded-full font-bold text-gray-400">{serverFiles.length} file</span>
        </div>
        
        <div className="bg-gray-50 rounded-2xl border border-gray-100 p-2 max-h-64 overflow-y-auto">
          {serverFiles.length === 0 ? (
            <div className="py-10 text-center">
              <p className="text-gray-400 text-xs italic">Thư mục hiện đang trống.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-1">
              {serverFiles.map((f, i) => (
                <div key={i} className="flex justify-between items-center p-3 hover:bg-white hover:shadow-sm rounded-xl transition-all group border-b border-gray-100 last:border-0">
                  <div className="flex items-center gap-3 truncate pr-4">
                    <div className="bg-blue-100 p-2 rounded-lg group-hover:bg-blue-600 transition-colors">
                      <File size={16} className="text-blue-600 group-hover:text-white" />
                    </div>
                    <span className="text-sm text-gray-700 font-medium truncate">{f.name}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                     <span className="text-[10px] text-gray-400 font-mono italic">{f.size} MB</span>
                     <CheckCircle size={14} className="text-green-500" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TransferSection;