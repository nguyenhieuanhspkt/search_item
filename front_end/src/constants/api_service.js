// src/api_service.js
import axios from "axios";

const API_BASE = "http://10.156.43.54:8000";

const api = {
  // Kiểm tra trạng thái hệ thống
  getSystemStatus: async () => {
    try {
      const response = await axios.get(`${API_BASE}/system-status`, {
        timeout: 5000,
      });
      return response.data;
    } catch (error) {
      console.error("Lỗi khi gọi API getSystemStatus:", error);
      return { status: "error", message: "Lỗi kết nối Server" };
    }
  },

  // Tìm kiếm đơn lẻ (Gửi dưới dạng Form Data để khớp với Backend cũ)
  searchQuery: async (text) => {
    const formData = new FormData();
    formData.append("query", text);
    try {
      const response = await axios.post(`${API_BASE}/search`, formData);
      return response.data; // Trả về mảng kết quả
    } catch (error) {
      return { error: error.message };
    }
  },

  // --- HÀM MỚI: Thẩm định hàng loạt (Bulk Match) ---
  // Dữ liệu truyền vào là mảng: [{stt: "1", ten: "...", tskt: "...", dvt: "..."}, ...]
  bulkMatch: async (items) => {
    try {
      // Gửi mảng JSON trực tiếp (không dùng FormData)
      const response = await axios.post(`${API_BASE}/api/bulk-match`, items);
      return response.data; // Trả về { status: 'success', data: [...] }
    } catch (error) {
      console.error("Lỗi Bulk Match:", error);
      return { status: "error", message: error.message };
    }
  },

  // --- HÀM MỚI: Trích xuất file Word ---
  extractWord: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await axios.post(`${API_BASE}/extract-word`, formData);
    return response.data;
  },

  // Rebuild Index (Dùng hàm này trong AdminSection)
  rebuildIndex: async (file, password) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", password);
    try {
      const response = await axios.post(
        `${API_BASE}/admin/rebuild-index`,
        formData,
      );
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },
};

export default api;
