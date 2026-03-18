import React, { useState, useEffect } from "react";
import { Search, FileText, Settings } from "lucide-react"; // Import thêm icon
import Sidebar from "./components/Sidebar";
import SearchSection from "./components/SearchSection";
import WordSection from "./components/WordSection";
// Thêm import này ở đầu file App.jsx
import AdminSection from "./components/AdminSection";
import api from "./constants/api_service";

function App() {
  const [activeMenu, setActiveMenu] = useState("search");
  const [status, setStatus] = useState({
    status: "loading",
    message: "Đang kết nối...",
  });

  // 1. Khai báo danh sách Menu ở đây để Sidebar có dữ liệu để hiển thị
  const menuItems = [
    { id: "search", label: "Tìm kiếm đơn lẻ", icon: <Search size={20} /> },
    { id: "word", label: "Thẩm định File Word", icon: <FileText size={20} /> },
    { id: "admin", label: "Quản trị hệ thống", icon: <Settings size={20} /> },
  ];

  useEffect(() => {
    api.getSystemStatus().then((res) => setStatus(res));
  }, []);

  return (
    // Chỉnh lại bg-[#0e1117] cho đồng bộ với Sidebar tối (Dark theme)
    <div className="flex h-screen bg-[#0e1117]">
      <Sidebar
        activeMenu={activeMenu}
        setActiveMenu={setActiveMenu}
        status={status}
        menuItems={menuItems} // 2. BẮT BUỘC PHẢI TRUYỀN DÒNG NÀY!
      />
      
      {/* Phần main content */}
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