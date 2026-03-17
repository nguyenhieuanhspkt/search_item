import React from "react";
import { ClipboardCheck } from "lucide-react";

const PasteZone = ({ onPaste }) => (
  <div
    onPaste={onPaste}
    className="border-2 border-dashed border-blue-200 bg-blue-50 h-48 flex flex-col items-center justify-center rounded-2xl cursor-pointer hover:bg-blue-100 transition-all group"
  >
    <div className="bg-white p-4 rounded-full shadow-sm mb-3 group-hover:scale-110 transition-transform">
      <ClipboardCheck className="w-8 h-8 text-blue-500" />
    </div>
    <p className="text-blue-700 font-bold text-lg">Nhấn Ctrl + V để dán bảng</p>
    <p className="text-blue-400 text-sm mt-1">
      Hỗ trợ copy trực tiếp từ bảng Word hoặc Excel
    </p>
  </div>
);

export default PasteZone;
