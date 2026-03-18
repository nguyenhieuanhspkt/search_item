import React, { useState } from 'react';
import { ShieldCheck, Menu, X, Search, FileText, Settings } from 'lucide-react';

const Sidebar = ({ 
  status = { status: 'offline', message: '' }, 
  activeMenu = 'search', 
  setActiveMenu = () => {}, 
  menuItems = [] 
}) => {
  // Trạng thái đóng/mở trên điện thoại
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* NÚT MENU MOBILE: Chỉ hiện khi Sidebar đang đóng và ở màn hình nhỏ */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="md:hidden fixed top-4 left-4 z-[100] p-2 bg-[#1a1c24] border border-gray-700 rounded-lg text-white"
        >
          <Menu size={24} />
        </button>
      )}

      {/* LỚP NỀN ĐEN: Click vào đây để đóng Sidebar trên mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[110] md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* NỘI DUNG SIDEBAR */}
      <aside className={`
        fixed inset-y-0 left-0 z-[120] w-64 bg-[#0e1117] border-r border-gray-800
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? "translate-x-0" : "-translate-x-full"} 
        md:relative md:translate-x-0 md:flex md:flex-col md:h-screen
      `}>
        
        {/* LOGO & NÚT ĐÓNG */}
        <div className="p-6 md:p-8 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <ShieldCheck className="text-blue-500" size={28} />
            <h1 className="text-lg font-bold text-white whitespace-nowrap">Thẩm định v2.6</h1>
          </div>
          <button onClick={() => setIsOpen(false)} className="md:hidden text-gray-400">
            <X size={24} />
          </button>
        </div>

        {/* TRẠNG THÁI SERVER (Chống tràn chữ) */}
        <div className="px-6 mb-6">
          <div className={`p-3 rounded-lg border text-[10px] break-all ${
              status?.status === "ready"
                ? "bg-green-900/10 border-green-800/50 text-green-400"
                : "bg-red-900/10 border-red-800/50 text-red-400"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className={status?.status === "ready" ? "animate-pulse" : ""}>●</span> 
              <span className="font-bold uppercase">{status?.status || "OFFLINE"}</span>
            </div>
            <p className="opacity-70 leading-tight">
              {status?.message || "Đang kết nối..."}
            </p>
          </div>
        </div>

        {/* MENU ĐIỀU HƯỚNG: Nối dây setActiveMenu để bấm được */}
        <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
          {menuItems && menuItems.length > 0 ? (
            menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveMenu(item.id); // Đổi trang
                  setIsOpen(false);      // Đóng sidebar trên mobile
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  activeMenu === item.id
                    ? "bg-[#262730] text-white shadow-md border border-gray-700"
                    : "text-gray-400 hover:bg-[#1a1c24] hover:text-gray-200"
                }`}
              >
                {/* Hiển thị Icon từ Props */}
                <span className="flex-shrink-0">{item.icon}</span>
                <span className="font-medium text-sm">{item.label}</span>
              </button>
            ))
          ) : (
            <p className="text-gray-600 text-xs text-center">Không có menu</p>
          )}
        </nav>

        {/* FOOTER */}
        <div className="p-4 border-t border-gray-800/50 text-[10px] text-gray-500 text-center font-mono">
          Vinh Tan 4 - Appraisal System
        </div>
      </aside>
    </>
  );
};

export default Sidebar;