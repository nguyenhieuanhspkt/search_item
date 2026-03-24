export const mapMeiliToUI = (item) => ({
  matchHeThong: item["TÊN VẬT TƯ (NXT)"] || "Không rõ tên",
  erp: item["Mã vật tư"] || "N/A",
  chung_loai: item["CHỦNG LOẠI"] || "Vật tư khác",
  dvt: item["ĐƠN VỊ TÍNH"] || "Cái",
  hang: item["HÃNG SẢN XUẤT"] || "Không xác định",
  tskt: item["QUY CÁCH/ THÔNG SỐ KỸ THUẬT (THEO PHÊ DUYỆT)"] || item["DIỄN GIẢI CHI TIẾT VẬT TƯ"],
  score: 100, // Tìm mã hiệu khớp tuyệt đối nên để 100
  engine: "Meilisearch (Core2)"
});