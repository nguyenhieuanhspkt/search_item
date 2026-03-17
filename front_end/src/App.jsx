import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import SearchSection from "./components/SearchSection";
import WordSection from "./components/WordSection";
import api from "./constants/api_service";

function App() {
  const [activeMenu, setActiveMenu] = useState("search");
  const [status, setStatus] = useState({
    status: "loading",
    message: "Đang kết nối...",
  });

  useEffect(() => {
    api.getSystemStatus().then((res) => setStatus(res));
  }, []);

  return (
    <div className="flex h-screen bg-[#f0f2f6]">
      {" "}
      {/* Lệnh FLEX này chia cột trái/phải */}
      <Sidebar
        activeMenu={activeMenu}
        setActiveMenu={setActiveMenu}
        status={status}
      />
      <main className="flex-1 overflow-y-auto p-12">
        <div className="max-w-5xl mx-auto bg-white p-10 rounded-2xl shadow-sm border border-gray-200">
          {activeMenu === "search" && <SearchSection />}
          {activeMenu === "word" && <WordSection />}
          {activeMenu === "admin" && (
            <div className="p-10 text-center italic text-gray-400">
              Chức năng Quản trị chưa mở...
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
