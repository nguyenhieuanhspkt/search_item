import React, { useState } from "react";
import { Search, Settings, Loader2, LogOut, ShieldCheck } from "lucide-react";
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

function App() {
  const [activeTab, setActiveTab] = useState("search");
  const [loginPass, setLoginPass] = useState("");
  const [file, setFile] = useState(null);

  // Triệu hồi Hooks (Giữ nguyên gốc của bạn)
  const { status, progress } = useSystem();
  const { query, setQuery, results, searching, handleSearch } = useSearch();
  const { isAdmin, login, logout, adminPassword } = useAuth();

  // Logic xử lý Upload (Giữ nguyên gốc của bạn)
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
      {/* HEADER - Thiết kế lại Tab ngang cho hiện đại */}
      <header
        style={{
          backgroundColor: "#fff",
          borderBottom: "1px solid #e2e8f0",
          padding: "1rem 0",
        }}
      >
        <div
          style={{
            maxWidth: "1000px",
            margin: "0 auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0 20px",
          }}
        >
          <h2 style={{ fontSize: "1.25rem", fontWeight: "bold", margin: 0 }}>
            🛡️ TỔ THẨM ĐỊNH v2.6
          </h2>
          <nav style={{ display: "flex", gap: "10px" }}>
            <button
              onClick={() => setActiveTab("search")}
              style={activeTab === "search" ? styles.tabActive : styles.tabBtn}
            >
              <Search size={18} /> Tìm kiếm
            </button>
            <button
              onClick={() => setActiveTab("admin")}
              style={activeTab === "admin" ? styles.tabActive : styles.tabBtn}
            >
              <Settings size={18} /> Quản trị
            </button>
          </nav>
        </div>
      </header>

      {/* MAIN CONTENT - Căn giữa chuẩn Streamlit */}
      <main
        style={{ maxWidth: "1000px", margin: "2rem auto", padding: "0 20px" }}
      >
        <StatusBar status={status} />

        {/* PROGRESS BAR */}
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

        {/* TAB TÌM KIẾM */}
        {activeTab === "search" && (
          <>
            <section
              style={{ ...styles.card, padding: "24px", borderRadius: "12px" }}
            >
              <textarea
                style={{
                  ...styles.textarea,
                  minHeight: "120px",
                  fontSize: "16px",
                }}
                placeholder="Nhập nội dung cần thẩm định..."
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
                  <Loader2
                    style={{ animation: "spin 1s linear infinite" }}
                    size={20}
                  />
                ) : (
                  "🚀 BẮT ĐẦU THẨM ĐỊNH"
                )}
              </button>
            </section>

            {/* RÁP COMPONENT KẾT QUẢ VÀO ĐÂY */}
            <SearchContainer searching={searching} results={results} />
          </>
        )}

        {/* TAB QUẢN TRỊ */}
        {activeTab === "admin" && (
          <section
            style={{ ...styles.card, padding: "30px", borderRadius: "12px" }}
          >
            {!isAdmin ? (
              <div style={{ textAlign: "center" }}>
                <ShieldCheck
                  size={48}
                  color="#3b82f6"
                  style={{ margin: "0 auto 1rem" }}
                />
                <h3 style={{ marginBottom: "20px" }}>Xác thực Quản trị</h3>
                <input
                  type="password"
                  style={{
                    ...styles.textarea,
                    height: "45px",
                    textAlign: "center",
                    marginBottom: "15px",
                  }}
                  placeholder="Mật mã Admin..."
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
                  <h3 style={{ margin: 0 }}>📦 Cập nhật Database AI</h3>
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
                    <LogOut size={16} /> Thoát
                  </button>
                </div>
                <div
                  style={{
                    padding: "30px",
                    border: "2px dashed #e2e8f0",
                    borderRadius: "8px",
                    textAlign: "center",
                    background: "#f8fafc",
                    marginBottom: "20px",
                  }}
                >
                  <input
                    type="file"
                    accept=".xlsx, .xls"
                    onChange={(e) => setFile(e.target.files[0])}
                  />
                </div>
                <button
                  style={{
                    ...styles.btnPrimary,
                    width: "100%",
                    backgroundColor: file ? "#059669" : "#94a3b8",
                  }}
                  onClick={handleUpload}
                >
                  CẬP NHẬT DATABASE
                </button>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
