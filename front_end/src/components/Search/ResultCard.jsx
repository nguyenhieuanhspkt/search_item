// Đây là mảnh ghép quan trọng nhất - bộ mặt của "Tổ Thẩm Định".
import React from "react";
import { Tag, ShieldCheck, Box, Factory } from "lucide-react";
import { styles } from "../../constants/styles";

const ResultCard = ({ item, index }) => (
  <div style={styles.resultCard}>
    <div style={styles.cardHeader}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <span style={styles.rankBadge}>TOP {index + 1}</span>
        <h3 style={styles.vattuTitle}>{item.ten}</h3>
      </div>
      <div
        style={{
          ...styles.scoreBadge,
          backgroundColor: item.final_score > 0.7 ? "#dcfce7" : "#fef3c7",
          color: item.final_score > 0.7 ? "#166534" : "#92400e",
        }}
      >
        Khớp: {Math.round(item.final_score * 100)}%
      </div>
    </div>

    <div style={styles.infoGrid}>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span style={styles.label}>
          <Tag size={12} /> Mã Vật Tư
        </span>
        <code style={styles.code}>{item.ma || "---"}</code>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span style={styles.label}>
          <ShieldCheck size={12} /> Mã ERP
        </span>
        <code style={styles.code}>{item.erp || "---"}</code>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span style={styles.label}>
          <Box size={12} /> Đơn vị tính
        </span>
        <span style={{ fontSize: "14px", fontWeight: "600" }}>{item.dvt}</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span style={styles.label}>
          <Factory size={12} /> Hãng sản xuất
        </span>
        <span style={{ fontSize: "14px", fontWeight: "600" }}>
          {item.hang || "N/A"}
        </span>
      </div>
    </div>

    {/* Thông số kỹ thuật */}
    <div style={{ padding: "0 24px 24px 24px" }}>
      <div
        style={{
          backgroundColor: "#f8fafc",
          padding: "16px",
          borderRadius: "12px",
          border: "1px solid #f1f5f9",
        }}
      >
        <span style={styles.label}>Thông số kỹ thuật / Mã hiệu</span>
        <p
          style={{
            margin: "8px 0 0 0",
            fontSize: "14px",
            color: "#475569",
            lineHeight: "1.6",
          }}
        >
          {item.ts || "Không có dữ liệu chi tiết"}
        </p>
      </div>
    </div>
  </div>
);

export default ResultCard;
