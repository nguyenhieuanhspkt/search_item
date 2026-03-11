import React, { useState } from "react";
import {
  Search,
  FileText,
  Settings,
  Loader2,
  LogOut,
  ShieldCheck,
} from "lucide-react";
import axios from "axios";

// Import các "não bộ" (Hooks)
import { useSystem } from "./hooks/useSystem";
import { useSearch } from "./hooks/useSearch";
import { useAuth } from "./hooks/useAuth"; // Hook mới cho xác thực

// Import các "ngoại hình" (Styles & Config)
import { styles } from "./constants/styles";
import { API_BASE } from "./constants/config";
import StatusBar from "./components/Layout/StatusBar";
import ResultCard from "./components/Search/ResultCard";

function App() {
  const [activeTab, setActiveTab] = useState("search");

  // Triệu hồi các Hooks
  const { status, progress } = useSystem();
  const { query, setQuery, results, searching, handleSearch } = useSearch();
  const { isAdmin, login, logout, adminPassword } = useAuth();

  // State cục bộ cho Admin
  const [loginPass, setLoginPass] = useState("");
  const [file, setFile] = useState(null);

  // Hàm xử lý Upload Database
  const handleUpload = async () => {
    if (!file) return alert("Vui lòng chọn file Excel!");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", adminPassword);

    try {
      const res = await axios.post(`${API_BASE}/admin/upload-excel`, formData);
      if (res.data.error) {
        alert("Lỗi: " + res.data.error);
      } else {
        alert("🚀 Đã bắt đầu nạp dữ liệu vào AI!");
        setFile(null); // Reset file sau khi chọn
      }
    } catch (err) {
      console.error("Lỗi kết nối server khi upload!", err);
      alert("Lỗi kết nối server khi upload!");
    }
  };

  return (
    <div style={styles.app}>
      {/* SIDEBAR - Thanh điều hướng */}
      <aside style={styles.sidebar}>
        <h2 style={styles.logo}>🛡️ TỔ THẨM ĐỊNH v2.6</h2>
        <nav style={styles.nav}>
          <button
            onClick={() => setActiveTab("search")}
            style={activeTab === "search" ? styles.navActive : styles.navBtn}
          >
            <Search size={18} /> Tìm đơn lẻ
          </button>
          <button
            onClick={() => setActiveTab("word")}
            style={activeTab === "word" ? styles.navActive : styles.navBtn}
          >
            <FileText size={18} /> Thẩm định Word
          </button>
          <button
            onClick={() => setActiveTab("admin")}
            style={activeTab === "admin" ? styles.navActive : styles.navBtn}
          >
            <Settings size={18} /> Quản trị
          </button>
        </nav>
      </aside>

      {/* MAIN CONTENT - Nội dung chính */}
      <main style={styles.mainContent}>
        <StatusBar status={status} />

        {/* Tiến độ xử lý file chung cho hệ thống */}
        {progress.percent > 0 && progress.percent < 100 && (
          <div style={styles.progressContainer}>
            <div style={styles.progressHeader}>
              <span style={styles.taskText}>⏳ {progress.task}</span>
              <span style={styles.percentText}>{progress.percent}%</span>
            </div>
            <div style={styles.progressBgFull}>
              <div
                style={{
                  ...styles.progressFillFull,
                  width: `${progress.percent}%`,
                }}
              />
            </div>
          </div>
        )}

        {/* VIEW: TÌM KIẾM ĐƠN LẺ */}
        {activeTab === "search" && (
          <div style={styles.viewContainer}>
            <div style={styles.searchSection}>
              <textarea
                style={styles.textarea}
                placeholder="Nhập nội dung cần thẩm định (Tên vật tư, thông số, mã hiệu...)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                style={styles.btnPrimary}
                onClick={() => handleSearch(status.type)}
                disabled={searching || status.type !== "ready"}
              >
                {searching ? (
                  <Loader2 className="spin" size={20} />
                ) : (
                  "🚀 BẮT ĐẦU THẨM ĐỊNH"
                )}
              </button>
            </div>

            <div style={styles.resultsContainer}>
              {results.length > 0
                ? results.map((item, index) => (
                    <ResultCard key={index} item={item} index={index} />
                  ))
                : !searching && (
                    <div
                      style={{
                        textAlign: "center",
                        color: "#94a3b8",
                        marginTop: "40px",
                      }}
                    >
                      Sẵn sàng tiếp nhận dữ liệu thẩm định.
                    </div>
                  )}
            </div>
          </div>
        )}

        {/* VIEW: QUẢN TRỊ (Đã cập nhật logic login/upload) */}
        {activeTab === "admin" && (
          <div style={styles.viewContainer}>
            {!isAdmin ? (
              /* GIAO DIỆN ĐĂNG NHẬP */
              <div style={styles.searchSection}>
                <h3
                  style={{
                    marginBottom: "15px",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                >
                  <ShieldCheck size={24} color="#3b82f6" /> Xác thực Quản trị
                  viên
                </h3>
                <input
                  type="password"
                  style={{
                    ...styles.textarea,
                    height: "45px",
                    marginBottom: "15px",
                  }}
                  placeholder="Nhập mật mã quản trị..."
                  onChange={(e) => setLoginPass(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && login(loginPass)}
                />
                <button
                  style={styles.btnPrimary}
                  onClick={() => login(loginPass)}
                >
                  ĐĂNG NHẬP
                </button>
              </div>
            ) : (
              /* GIAO DIỆN UPLOAD KHI ĐÃ ĐĂNG NHẬP */
              <div style={styles.searchSection}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "20px",
                  }}
                >
                  <h3 style={{ margin: 0 }}>🚀 Khu vực Quản trị</h3>
                  <button
                    onClick={logout}
                    style={{
                      color: "#ef4444",
                      border: "1px solid #fee2e2",
                      background: "#fef2f2",
                      padding: "5px 12px",
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

                <p style={{ color: "#64748b", fontSize: "14px" }}>
                  Chào mừng Admin! Hãy chọn file Excel danh mục vật tư mới nhất
                  để nạp vào hệ thống AI.
                </p>

                <div
                  style={{
                    margin: "20px 0",
                    padding: "20px",
                    border: "2px dashed #e2e8f0",
                    borderRadius: "8px",
                    textAlign: "center",
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
                    backgroundColor: file ? "#059669" : "#94a3b8",
                  }}
                  onClick={handleUpload}
                  disabled={!file}
                >
                  CẬP NHẬT DATABASE
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
