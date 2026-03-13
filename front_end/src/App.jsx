import React, { useState } from "react";
import {
  Search,
  Settings,
  Loader2,
  LogOut,
  ShieldCheck,
  FileText,
  ClipboardCheck,
} from "lucide-react";
import axios from "axios";

// IMPORT CÁC NÃO BỘ (Hooks)
import { useSystem } from "./hooks/useSystem";
import { useSearch } from "./hooks/useSearch";
import { useAuth } from "./hooks/useAuth";

// IMPORT NGOẠI HÌNH (Styles & Config)
import { styles } from "./constants/styles";
import { API_BASE } from "./constants/config";

// IMPORT COMPONENTS
import StatusBar from "./components/Layout/StatusBar";
import SearchContainer from "./components/Search/SearchContainer";
import BulkMatch from "./components/Bulk/BulkMatch"; // Component mới chúng ta vừa viết

function App() {
  // Đổi mặc định sang 'bulk' cho sếp dùng luôn
  const [activeTab, setActiveTab] = useState("bulk");
  const [loginPass, setLoginPass] = useState("");
  const [file, setFile] = useState(null);

  // Triệu hồi Hooks
  const { status, progress } = useSystem();
  const { query, setQuery, results, searching, handleSearch } = useSearch();
  const { isAdmin, login, logout, adminPassword } = useAuth();

  // Logic xử lý Upload Database
  const handleUpload = async () => {
    if (!file) return alert("Vui lòng chọn file Excel!");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", adminPassword);

    try {
      const res = await axios.post(`${API_BASE}/admin/upload-excel`, formData);
      if (res.data.error) alert("Lỗi: " + res.data.error);
      else {
        alert("🚀 Đã bắt đầu nạp dữ liệu vào AI!");
        setFile(null);
      }
    } catch (err) {
      console.error(err);
      alert("Lỗi kết nối server!");
    }
  };

  return (
    <div
      style={{
        ...styles.app,
        backgroundColor: "#f0f2f6",
        minHeight: "100vh",
        display: "block",
      }}
    >
      {/* HEADER - Navigation Bar */}
      <header
        style={{
          backgroundColor: "#fff",
          borderBottom: "1px solid #e2e8f0",
          padding: "1rem 0",
          sticky: "top",
          zIndex: 100,
        }}
      >
        <div
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0 20px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.5rem" }}>🛡️</span>
            <div>
              <h2
                style={{
                  fontSize: "1.1rem",
                  fontWeight: "bold",
                  margin: 0,
                  color: "#1e293b",
                }}
              >
                TỔ THẨM ĐỊNH AI
              </h2>
              <p
                style={{
                  fontSize: "0.7rem",
                  margin: 0,
                  color: "#64748b",
                  letterSpacing: "1px",
                }}
              >
                VERSION 2.6 PRO
              </p>
            </div>
          </div>

          <nav
            style={{
              display: "flex",
              gap: "8px",
              background: "#f1f5f9",
              padding: "4px",
              borderRadius: "8px",
            }}
          >
            <button
              onClick={() => setActiveTab("bulk")}
              style={
                activeTab === "bulk"
                  ? {
                      ...styles.tabActive,
                      boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    }
                  : styles.tabBtn
              }
            >
              <ClipboardCheck size={18} /> Đối soát Word
            </button>
            <button
              onClick={() => setActiveTab("search")}
              style={
                activeTab === "search"
                  ? {
                      ...styles.tabActive,
                      boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    }
                  : styles.tabBtn
              }
            >
              <Search size={18} /> Tra cứu lẻ
            </button>
            <button
              onClick={() => setActiveTab("admin")}
              style={
                activeTab === "admin"
                  ? {
                      ...styles.tabActive,
                      boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    }
                  : styles.tabBtn
              }
            >
              <Settings size={18} /> Hệ thống
            </button>
          </nav>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main
        style={{ maxWidth: "1200px", margin: "2rem auto", padding: "0 20px" }}
      >
        {/* Luôn hiển thị trạng thái hệ thống và tiến trình nạp dữ liệu */}
        <StatusBar status={status} />

        {progress && progress.percent > 0 && progress.percent < 100 && (
          <div
            style={{
              background: "#fff",
              padding: "15px",
              borderRadius: "10px",
              marginBottom: "1.5rem",
              boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "8px",
              }}
            >
              <span style={{ fontWeight: 500 }}>⏳ {progress.task}</span>
              <span style={{ color: "#3b82f6", fontWeight: "bold" }}>
                {progress.percent}%
              </span>
            </div>
            <div
              style={{
                width: "100%",
                height: "8px",
                background: "#eee",
                borderRadius: "4px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${progress.percent}%`,
                  height: "100%",
                  background: "#3b82f6",
                  transition: "0.3s",
                }}
              />
            </div>
          </div>
        )}

        {/* PHÂN THÂN THEO TAB */}

        {/* 1. TAB ĐỐI SOÁT HÀNG LOẠT (MỚI) */}
        {activeTab === "bulk" && (
          <div className="animate-fadeIn">
            <BulkMatch />
          </div>
        )}

        {/* 2. TAB TÌM KIẾM LẺ */}
        {activeTab === "search" && (
          <div className="animate-fadeIn">
            <section
              style={{
                ...styles.card,
                padding: "24px",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
              }}
            >
              <h3
                style={{
                  marginTop: 0,
                  marginBottom: "1rem",
                  fontSize: "1rem",
                  color: "#475569",
                }}
              >
                🔍 Tra cứu vật tư đơn lẻ
              </h3>
              <textarea
                style={{
                  ...styles.textarea,
                  minHeight: "100px",
                  fontSize: "16px",
                }}
                placeholder="Nhập tên vật tư hoặc thông số cần tìm..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                style={{
                  ...styles.btnPrimary,
                  width: "100%",
                  marginTop: "1rem",
                  height: "50px",
                  fontWeight: "bold",
                }}
                onClick={() => handleSearch(status?.type)}
                disabled={searching || status?.type !== "ready"}
              >
                {searching ? (
                  <Loader2 className="animate-spin" size={20} />
                ) : (
                  "🚀 TÌM KIẾM NGAY"
                )}
              </button>
            </section>
            <SearchContainer searching={searching} results={results} />
          </div>
        )}

        {/* 3. TAB QUẢN TRỊ */}
        {activeTab === "admin" && (
          <section
            style={{ ...styles.card, padding: "30px", borderRadius: "12px" }}
          >
            {!isAdmin ? (
              <div
                style={{
                  textAlign: "center",
                  maxWidth: "400px",
                  margin: "0 auto",
                }}
              >
                <ShieldCheck
                  size={48}
                  color="#3b82f6"
                  style={{ margin: "0 auto 1rem" }}
                />
                <h3 style={{ marginBottom: "20px" }}>
                  Xác thực quyền quản trị
                </h3>
                <input
                  type="password"
                  style={{
                    ...styles.textarea,
                    height: "45px",
                    textAlign: "center",
                    marginBottom: "15px",
                  }}
                  placeholder="Nhập mật mã..."
                  onChange={(e) => setLoginPass(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && login(loginPass)}
                />
                <button
                  style={{ ...styles.btnPrimary, width: "100%" }}
                  onClick={() => login(loginPass)}
                >
                  ĐĂNG NHẬP
                </button>
              </div>
            ) : (
              <div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "20px",
                  }}
                >
                  <h3 style={{ margin: 0 }}>📦 Quản lý Cơ sở dữ liệu AI</h3>
                  <button
                    onClick={logout}
                    style={{
                      color: "#ef4444",
                      border: "1px solid #fee2e2",
                      background: "#fef2f2",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "5px",
                    }}
                  >
                    <LogOut size={16} /> Đăng xuất
                  </button>
                </div>
                <div
                  style={{
                    padding: "40px",
                    border: "2px dashed #cbd5e1",
                    borderRadius: "12px",
                    textAlign: "center",
                    background: "#f8fafc",
                    marginBottom: "20px",
                  }}
                >
                  <input
                    type="file"
                    accept=".xlsx, .xls"
                    onChange={(e) => setFile(e.target.files[0])}
                    style={{ marginBottom: "10px" }}
                  />
                  <p style={{ fontSize: "0.8rem", color: "#64748b" }}>
                    Chọn file Excel danh mục vật tư chuẩn (.xlsx)
                  </p>
                </div>
                <button
                  style={{
                    ...styles.btnPrimary,
                    width: "100%",
                    backgroundColor: file ? "#059669" : "#94a3b8",
                  }}
                  onClick={handleUpload}
                  disabled={!file}
                >
                  {file ? "CẬP NHẬT DATABASE NGAY" : "VUI LÒNG CHỌN FILE"}
                </button>
              </div>
            )}
          </section>
        )}
      </main>

      <footer
        style={{
          textAlign: "center",
          padding: "2rem",
          color: "#94a3b8",
          fontSize: "0.8rem",
        }}
      >
        Hệ thống hỗ trợ thẩm định vật tư bằng trí tuệ nhân tạo © 2024
      </footer>
    </div>
  );
}

export default App;
