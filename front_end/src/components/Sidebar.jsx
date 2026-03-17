import React from "react";
import { Search, FileText, Settings, ShieldCheck } from "lucide-react";

const Sidebar = ({ activeMenu, setActiveMenu, status }) => {
  const menuItems = [
    { id: "search", label: "Tìm kiếm đơn lẻ", icon: <Search size={20} /> },
    { id: "word", label: "Thẩm định File Word", icon: <FileText size={20} /> },
    { id: "admin", label: "Quản trị hệ thống", icon: <Settings size={20} /> },
  ];

  return (
    <aside className="w-72 bg-[#0e1117] text-[#fafafa] h-screen flex flex-col flex-shrink-0 border-r border-gray-800 shadow-2xl">
      <div className="p-8">
        <div className="flex items-center gap-3 text-white mb-2">
          <ShieldCheck className="text-blue-500" size={32} />
          <h1 className="text-xl font-bold">Thẩm định v2.6</h1>
        </div>
      </div>

      <div className="px-6 mb-6">
        <div
          className={`p-3 rounded-lg border text-xs ${
            status?.status === "ready"
              ? "bg-green-900/20 border-green-800 text-green-400"
              : "bg-red-900/20 border-red-800 text-red-400"
          }`}
        >
          ● {status?.message || "Mất kết nối Server"}
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveMenu(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeMenu === item.id
                ? "bg-[#262730] text-white shadow-md"
                : "text-gray-400 hover:bg-[#1a1c24]"
            }`}
          >
            {item.icon}
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
