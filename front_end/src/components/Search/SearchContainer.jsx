import React from "react";
import { Loader2, Inbox } from "lucide-react";
import ResultCard from "./ResultCard"; // Cùng folder nên import trực tiếp

const SearchContainer = ({ searching, results }) => {
  return (
    <div style={localStyles.container}>
      {searching ? (
        // Hiển thị Loading khi đang tìm
        <div style={localStyles.statusArea}>
          <Loader2
            style={{ animation: "spin 1s linear infinite" }}
            size={32}
            color="#3b82f6"
          />
          <p style={{ marginTop: "12px", color: "#64748b" }}>
            AI đang phân tích dữ liệu...
          </p>
        </div>
      ) : results && results.length > 0 ? (
        // Hiển thị danh sách kết quả
        <div style={localStyles.list}>
          {results.map((item, index) => (
            <ResultCard key={index} item={item} index={index} />
          ))}
        </div>
      ) : (
        // Hiển thị trạng thái trống (Empty State) - Giúp resize page mượt hơn
        <div style={localStyles.emptyArea}>
          <Inbox size={48} color="#cbd5e1" />
          <p style={{ marginTop: "12px", color: "#94a3b8" }}>
            Sẵn sàng tiếp nhận dữ liệu thẩm định.
          </p>
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

const localStyles = {
  container: { marginTop: "20px", minHeight: "300px" },
  statusArea: {
    textAlign: "center",
    padding: "40px",
    background: "#fff",
    borderRadius: "8px",
  },
  emptyArea: {
    textAlign: "center",
    padding: "60px",
    background: "#f8fafc",
    borderRadius: "12px",
    border: "2px dashed #e2e8f0",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  list: { display: "flex", flexDirection: "column", gap: "15px" },
};

export default SearchContainer;
