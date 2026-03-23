// src/App.jsx
import React, { useState, useEffect } from "react";
import { Search, FileText, Settings } from "lucide-react"; 
import Sidebar from "./components/Sidebar";
import SearchSection from "./components/SearchSection";
import WordSection from "./components/WordSection";
import AdminSection from "./components/AdminSection";
import TransferSection from "./components/TransferSection"; // Import module mới
import api from "./constants/api_service";

function App() {
  const [activeMenu, setActiveMenu] = useState("search");
  const [status, setStatus] = useState({ status: "loading", message: "Đang kết nối..." });

  // --- BƯỚC SỬA Ở ĐÂY ---
  // Kiểm tra xem người dùng có đang gõ /transfer trên thanh địa chỉ không
  const isTransferRoute = window.location.pathname === "/transfer";

  useEffect(() => {
    api.getSystemStatus().then((res) => setStatus(res));
  }, []);

  // NẾU LÀ ROUTE TRANSFER: Trả về giao diện upload luôn, không hiện Sidebar của Hiếu
  if (isTransferRoute) {
    return (
      <div className="min-h-screen bg-[#0e1117] flex items-center justify-center p-4">
        <div className="w-full max-w-2xl bg-white p-10 rounded-3xl shadow-2xl">
           <TransferSection />
        </div>
      </div>
    );
  }

  // --- CÁC LOGIC CŨ CỦA HIẾU GIỮ NGUYÊN ---
  const menuItems = [
    { id: "search", label: "Tìm kiếm đơn lẻ", icon: <Search size={20} /> },
    { id: "word", label: "Thẩm định File Word", icon: <FileText size={20} /> },
    { id: "admin", label: "Quản trị hệ thống", icon: <Settings size={20} /> },
  ];

  return (
    <div className="flex h-screen bg-[#0e1117]">
      <Sidebar
        activeMenu={activeMenu}
        setActiveMenu={setActiveMenu}
        status={status}
        menuItems={menuItems}
      />
      <main className="flex-1 overflow-y-auto p-4 md:p-12">
        <div className="max-w-5xl mx-auto bg-white p-6 md:p-10 rounded-2xl shadow-sm border border-gray-200">
          {activeMenu === "search" && <SearchSection />}
          {activeMenu === "word" && <WordSection />}
          {activeMenu === "admin" && <AdminSection status={status} />}
        </div>
      </main>
    </div>
  );
}

export default App;