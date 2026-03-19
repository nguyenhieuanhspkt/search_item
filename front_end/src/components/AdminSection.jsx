
import React, { useState, useRef } from 'react';
import { Database, RefreshCw, HardDrive, ShieldAlert, Settings, FileSpreadsheet, Lock } from 'lucide-react';
import api from '../constants/api_service';

const AdminSection = ({ status }) => {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [password, setPassword] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [progress, setProgress] = useState(0); // Lưu % từ 0 - 100
  
  // Dùng ref để kích hoạt chọn file ẩn
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setMsg(`Đã chọn file: ${file.name}. Vui lòng nhập mật khẩu để xác nhận.`);
    }
  };

  const handleRebuild = async () => {
    // 1. Kiểm tra đầu vào (Giữ nguyên logic của bạn)
    if (!selectedFile) {
      setMsg("⚠️ Vui lòng chọn file Excel danh mục vật tư trước.");
      fileInputRef.current.click();
      return;
    }
    if (!password) {
      setMsg("⚠️ Vui lòng nhập mật khẩu Admin để thực hiện lệnh này.");
      return;
    }

    if (!window.confirm("Hành động này sẽ xóa dữ liệu cũ và nạp lại từ đầu. Bạn chắc chứ?")) return;

    setLoading(true);
    setProgress(0);
    setMsg("🚀 Khởi động tiến trình nạp dữ liệu...");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("password", password);

      // SỬ DỤNG FETCH ĐỂ ĐỌC STREAM (Thay vì dùng api_service cũ)
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/admin/rebuild-index`, {
        method: 'POST',
        body: formData,
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        lines.forEach(line => {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.replace('data: ', ''));
              
              if (data.status === "progress") {
                setProgress(data.percent);
                setMsg(`🔄 Đang phân loại AI: ${data.percent}% (${data.current}/${data.total})`);
              } else if (data.status === "info") {
                setMsg(data.message);
              } else if (data.status === "success") {
                setMsg("✅ " + data.message);
                setProgress(100);
                setSelectedFile(null);
                setPassword("");
              } else if (data.status === "error") {
                setMsg("❌ " + data.message);
                setLoading(false);
              }
            } catch (e) {
              console.error("Lỗi parse stream:", e);
            }
          }
        });
      }
    } catch (err) {
      setMsg("❌ Lỗi kết nối Server. Hãy kiểm tra Backend.");
    } finally {
      setLoading(false);
    }
  };

return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center gap-4 border-b pb-6">
        <div className="bg-orange-500/10 p-3 rounded-xl">
          <Settings className="text-orange-600" size={32} />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Quản trị hệ thống</h2>
          <p className="text-gray-500 text-sm">Cấu hình dữ liệu và phân loại AI (Vĩnh Tân 4)</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Thẻ Quản lý nạp dữ liệu */}
        <div className="p-8 border-2 border-dashed border-gray-200 rounded-3xl bg-white hover:border-blue-300 transition-all">
          <div className="flex items-center gap-3 mb-6 text-blue-600">
            <Database size={24} />
            <h3 className="font-bold text-lg">Cơ sở dữ liệu vật tư</h3>
          </div>

          <div className="space-y-4">
            {/* Nút chọn File - Vô hiệu hóa khi đang loading */}
            <div 
              onClick={() => !loading && fileInputRef.current.click()}
              className={`p-4 rounded-2xl border-2 border-dashed flex flex-col items-center justify-center gap-2 transition-all ${
                loading ? "bg-gray-50 border-gray-100 cursor-not-allowed opacity-60" :
                selectedFile ? "bg-green-50 border-green-200 cursor-pointer" : "bg-gray-50 border-gray-100 hover:bg-blue-50 cursor-pointer"
              }`}
            >
              <FileSpreadsheet className={selectedFile ? "text-green-500" : "text-gray-400"} size={40} />
              <span className="text-sm font-medium text-gray-600 text-center">
                {selectedFile ? selectedFile.name : "Nhấn để chọn file Excel danh mục (.xlsx)"}
              </span>
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                className="hidden" 
                accept=".xlsx, .xls"
                disabled={loading}
              />
            </div>

            {/* Ô nhập mật khẩu */}
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input 
                type="password"
                placeholder="Mật khẩu Admin"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-100 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm disabled:opacity-50"
              />
            </div>

            {/* Nút bấm xác nhận */}
            <button 
              onClick={handleRebuild}
              disabled={loading}
              className={`w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-black text-sm uppercase tracking-wider transition-all ${
                loading 
                  ? "bg-gray-200 text-gray-400 cursor-not-allowed" 
                  : "bg-blue-600 hover:bg-blue-700 text-white shadow-xl shadow-blue-100 active:scale-95"
              }`}
            >
              {loading ? (
                <RefreshCw size={20} className="animate-spin" />
              ) : (
                <RefreshCw size={20} />
              )}
              {loading ? "Đang xử lý dữ liệu AI..." : "Xác nhận nạp dữ liệu"}
            </button>

            {/* Hiển thị Progress Bar khi đang nạp - Đặt ngoài button */}
            {loading && (
              <div className="mt-4 p-4 bg-blue-50/50 rounded-2xl border border-blue-100 animate-in zoom-in-95 duration-300">
                <div className="flex justify-between text-[10px] font-bold text-blue-600 uppercase tracking-widest mb-2">
                  <span>Tiến độ đồng bộ dữ liệu</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="w-full h-2 bg-blue-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-600 transition-all duration-500 ease-out shadow-[0_0_8px_rgba(37,99,235,0.4)]"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Thẻ Thông số hệ thống */}
        <div className="p-8 border border-gray-100 rounded-3xl bg-gray-50/50 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-6 text-purple-600">
              <HardDrive size={24} />
              <h3 className="font-bold text-lg">Thông tin Model</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-white rounded-xl shadow-sm">
                <span className="text-gray-500 text-sm font-medium">Model cốt lõi:</span>
                <span className="font-black text-blue-600 text-xs px-2 py-1 bg-blue-50 rounded">BGE-M3 (Multilingual)</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-white rounded-xl shadow-sm">
                <span className="text-gray-500 text-sm font-medium">Trạng thái:</span>
                <span className="text-green-600 font-bold text-xs uppercase animate-pulse">● Online</span>
              </div>
              <div className="p-3 bg-white rounded-xl shadow-sm overflow-hidden">
                <span className="text-gray-500 text-sm font-medium block mb-2">Đường dẫn dữ liệu:</span>
                <div className="font-mono text-[9px] text-gray-400 break-all leading-relaxed">
                  {status?.message?.split('(')[1]?.replace(')', '') || "D:/Project/vattu_index"}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 flex items-start gap-2 text-[10px] text-gray-400 italic">
            <AlertCircle size={14} className="shrink-0" />
            Lưu ý: Sau khi nạp dữ liệu, hệ thống sẽ tự động phân loại chủng loại dựa trên AI và tệp cấu hình.
          </div>
        </div>
      </div>

      {/* Thông báo kết quả hoặc lỗi */}
      {msg && (
        <div className={`p-5 rounded-2xl border flex items-center gap-4 animate-in slide-in-from-bottom-4 duration-300 ${
          msg.includes("✅") ? "bg-green-50 border-green-100 text-green-700" : 
          msg.includes("❌") ? "bg-red-50 border-red-100 text-red-700" : "bg-blue-50 border-blue-100 text-blue-700"
        }`}>
          <div className={`p-2 rounded-full ${msg.includes("✅") ? "bg-green-100" : msg.includes("❌") ? "bg-red-100" : "bg-blue-100"}`}>
            <ShieldAlert size={20} />
          </div>
          <div className="flex flex-col">
             <span className="font-bold text-sm">{msg}</span>
             {loading && <span className="text-[10px] opacity-70">Vui lòng không đóng trình duyệt lúc này...</span>}
          </div>
        </div>
      )}
    </div>
  );
};

const AlertCircle = ({ size, className }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

export default AdminSection;