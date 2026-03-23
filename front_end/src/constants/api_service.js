// src/api_service.js
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL
console.log("Backend đang trỏ vào:", API_BASE); // Dòng này để Hiếu kiểm tra trong F12
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 6000, // Tăng lên 15s vì nạp AI lần đầu sẽ lâu
});

const api = {
  // Kiểm tra trạng thái hệ thống
  getSystemStatus: async () => {
    try {
      const response = await apiClient.get("/system-status");
      return response.data;
    } catch (error) {
      console.error("Lỗi khi gọi API getSystemStatus:", error);
      return { status: "error", message: "Lỗi kết nối Server" };
    }
  },

  // Tìm kiếm đơn lẻ (Gửi dưới dạng Form Data để khớp với Backend cũ)
  searchQuery: async (query, mode = "combined") => {
    const formData = new FormData();
    formData.append("query", query);
    formData.append("mode", mode);
    
    // Đã sửa: dùng apiClient để tự động nhận baseURL cổng 8000
    const response = await apiClient.post("/search", formData);
    console.log("Kết quả Search:", response.data);
    return response.data;
  },
  

  // --- HÀM MỚI: Thẩm định hàng loạt (Bulk Match) ---
  // Dữ liệu truyền vào là mảng: [{stt: "1", ten: "...", tskt: "...", dvt: "..."}, ...]
  bulkMatch: async (items) => {
    try {
      const response = await apiClient.post("/api/bulk-match", items);
      return response.data;
    } catch (error) {
      console.error("Lỗi Bulk Match:", error);
      return { status: "error", message: error.message };
    }
  },

  // --- HÀM MỚI: Trích xuất file Word ---
  extractWord: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post("/extract-word", formData);
    return response.data;
  },

  // Rebuild Index (Dùng hàm này trong AdminSection)
  rebuildIndex: async (file, password) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", password);
    try {
      const response = await apiClient.post("/admin/rebuild-index", formData);
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },
  uploadFiles: async (files, onProgress) => {
    const formData = new FormData();
    // Chú ý: Key phải là 'files' để khớp với tham số trong Python: List[UploadFile] = File(...)
    files.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await apiClient.post("/colleague/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 0, // KHÔNG GIỚI HẠN thời gian cho file 900MB
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percent);
          }
        },
      });
      return response.data;
    } catch (error) {
      console.error("Lỗi upload file:", error);
      throw error; // Quăng lỗi ra ngoài để UI xử lý
    }
  },
  // Lấy danh sách file đã có trong folder của Hiếu
  getUploadedFiles: async () => {
    try {
      const response = await apiClient.get("/colleague/files");
      return response.data;
    } catch (error) {
      console.error("Lỗi lấy danh sách file:", error);
      return [];
    }
  },
};

export default api;
