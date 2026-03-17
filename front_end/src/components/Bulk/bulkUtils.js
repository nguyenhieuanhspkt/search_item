import * as XLSX from "xlsx"; // Nhớ import thư viện này ở đầu file utils
import axios from "axios";
import { API_BASE } from "../../constants/config";

/**
 * Xử lý dữ liệu dán từ Clipboard (Word/Excel)
 */
export const processPasteData = (text) => {
  if (!text) return [];
  const rows = text.split("\n").filter((r) => r.trim() !== "");
  return rows
    .map((row, index) => {
      let cells = row.split("\t"); // Thử tách bằng Tab trước
      if (cells.length < 2) cells = row.split(/ {2,}/); // Nếu tạch, tách bằng 2 dấu cách
      const clean = cells.map((c) => c.trim());
      return {
        key: index, // Ant Design cần key để không lỗi
        stt: clean[0] || index + 1,
        ten: clean[1] || "",
        tskt: clean[2] || "",
        dvt: clean[3] || "",
      };
    })
    .filter(
      (item) => item.ten && !item.ten.toLowerCase().includes("tên vật tư"),
    );
};

/**
 * Gọi API đối soát AI
 */
export const sendMatchRequest = async (items) => {
  try {
    const response = await axios.post(`${API_BASE}/api/bulk-match`, items);
    return {
      success: true,
      data: response.data.data,
    };
  } catch (error) {
    console.error("Lỗi API Bulk Match:", error);
    return {
      success: false,
      message: error.response?.data?.message || "Lỗi kết nối Backend AI",
    };
  }
};

/**
 * Format dữ liệu để xuất Excel
 */
export const exportToExcel = (results) => {
  if (!results || results.length === 0) return;

  const data = results.map((res) => ({
    STT: res.stt,
    "Vật tư (Gốc)": res.word_name,
    "Vật tư khớp nhất (Kho)": res.stock_name,
    "Mã vật tư": res.full_stock_info?.ma || "",
    "Đơn vị tính": res.full_stock_info?.dvt || "",
    Hãng: res.full_stock_info?.hang || "",
    "Độ tin cậy": (res.score * 100).toFixed(0) + "%",
  }));

  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "KetQuaDoiSoat");
  XLSX.writeFile(wb, "Ket_qua_doi_soat_AI.xlsx");
};
