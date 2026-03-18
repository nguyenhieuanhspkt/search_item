import React, { useState } from 'react';
import { ShieldCheck, Menu, X } from 'lucide-react';

const Sidebar = ({ status, activeMenu, setActiveMenu, menuItems = [] }) => {
  // State để đóng/mở Sidebar trên điện thoại
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* 1. NÚT MENU (Chỉ hiện trên Mobile) */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="md:hidden fixed top-4 left-4 z-[60] p-2 bg-[#1a1c24] border border-gray-700 rounded-lg text-white shadow-lg"
        >
          <Menu size={24} />
        </button>
      )}

      {/* 2. LỚP NỀN MỜ (Overlay - Khi mở sidebar trên mobile) */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[70] md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* 3. NỘI DUNG SIDEBAR CHÍNH */}
      <aside className={`
        fixed inset-y-0 left-0 z-[80] w-72 bg-[#0e1117] border-r border-gray-800
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? "translate-x-0" : "-translate-x-full"} 
        md:relative md:translate-x-0 md:flex md:flex-col md:h-screen
      `}>
        
        {/* Header: Logo và Nút đóng */}
        <div className="p-6 md:p-8 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500/10 p-2 rounded-lg">
              <ShieldCheck className="text-blue-500" size={28} />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">Thẩm định</h1>
              <p className="text-[10px] text-gray-500 font-mono">Phiên bản v2.6</p>
            </div>
          </div>
          
          {/* Nút X đóng Sidebar (Chỉ hiện trên Mobile) */}
          <button onClick={() => setIsOpen(false)} className="md:hidden text-gray-400 hover:text-white">
            <X size={24} />
          </button>
        </div>

        {/* Trạng thái Kết nối Server */}
        <div className="px-6 mb-8">
          <div className={`p-4 rounded-2xl border transition-all duration-500 ${
              status?.status === "ready"
                ? "bg-green-500/5 border-green-500/20 text-green-400"
                : "bg-red-500/5 border-red-500/20 text-red-400"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2 h-2 rounded-full ${status?.status === "ready" ? "bg-green-500 animate-pulse" : "bg-red-500"}`}></span> 
              <span className="text-[10px] font-bold uppercase tracking-widest">
                {status?.status === "ready" ? "Hệ thống Sẵn sàng" : "Mất kết nối"}
              </span>
            </div>
            {/* Hiển thị message, tự động xuống dòng nếu quá dài */}
            <p className="text-[10px] opacity-70 break-all font-mono leading-relaxed">
              {status?.message || "Vui lòng kiểm tra Backend..."}
            </p>
          </div>
        </div>

        {/* Danh sách Menu điều hướng */}
        <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto">
          {/* Sử dụng optional chaining ?. và mặc định [] để chống lỗi map */}
          {menuItems?.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveMenu(item.id);
                setIsOpen(false); // Tự động đóng trên mobile sau khi chọn
              }}
              className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-200 group ${
                activeMenu === item.id
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-900/20"
                  : "text-gray-400 hover:bg-gray-800/50 hover:text-gray-200"
              }`}
            >
              <span className={`${activeMenu === item.id ? "text-white" : "group-hover:text-blue-400"}`}>
                {item.icon}
              </span>
              <span className="font-medium text-sm">{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Footer Sidebar */}
        <div className="p-6 border-t border-gray-800/50">
          <div className="bg-gray-800/30 rounded-xl p-3">
            <p className="text-[9px] text-gray-500 text-center leading-tight">
              Nhà máy Nhiệt điện Vĩnh Tân 4 <br/>
              Phát triển bởi Tổ Thẩm định © 2026
            </p>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;