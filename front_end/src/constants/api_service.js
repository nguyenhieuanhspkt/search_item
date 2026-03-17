// src/api_service.js
import axios from "axios";

const API_BASE = "http://localhost:8000";

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

  // Upload file Excel (Admin)
  uploadDatabase: async (file, password) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", password);
    try {
      const response = await axios.post(
        `${API_BASE}/admin/upload-excel`,
        formData,
      );
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },
  // --- HÀM MỚI: Trích xuất file Word ---
  extractWord: async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    // Lưu ý: Không cần set headers thủ công, axios sẽ tự nhận diện FormData
    const response = await axios.post(`${API_BASE}/extract-word`, formData);
    return response.data;
  },
};

export default api;
