import React from "react";
import { LayoutGrid } from "lucide-react";
import ResultCard from "./ResultCard";
import { styles } from "../../constants/styles"; // Đường dẫn tới file style của bạn

const SearchContainer = ({ searching, results }) => {
  if (searching) {
    return (
      <div style={styles.skeletonLoader}>
        <div className="skeleton-item" style={styles.skeletonItem}></div>
        <div className="skeleton-item" style={styles.skeletonItem}></div>
        <div className="skeleton-item" style={styles.skeletonItem}></div>
      </div>
    );
  }

  if (results.length > 0) {
    return (
      <div className="results-list active" style={{ marginTop: "20px" }}>
        {results.map((item, index) => (
          <ResultCard key={index} item={item} index={index} />
        ))}
      </div>
    );
  }

  return (
    <div style={styles.emptyState}>
      <LayoutGrid size={48} color="#e2e8f0" />
      <p style={{ marginTop: "1rem" }}>
        Nhập thông tin bên trên để bắt đầu thẩm định ngữ nghĩa AI
      </p>
      <div style={styles.hints}>
        <small>Gợi ý: "Bulông M10x50 thép mạ kẽm"</small>
      </div>
    </div>
  );
};

export default SearchContainer;
