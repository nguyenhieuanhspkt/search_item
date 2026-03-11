import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API_BASE } from "../constants/config";

export const useSystem = () => {
  const [status, setStatus] = useState({
    type: "loading",
    message: "Đang kết nối...",
  });
  const [progress, setProgress] = useState({ percent: 0, task: "Idle" });

  // Dùng useRef để đánh dấu lần mount đầu tiên (tránh các vấn đề về Strict Mode)
  const isMounted = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const resStatus = await axios.get(`${API_BASE}/system-status`);
      const resProgress = await axios.get(`${API_BASE}/admin/progress`);

      // Chỉ cập nhật State nếu component vẫn đang mount
      if (isMounted.current) {
        setStatus({
          type: resStatus.data.status,
          message: resStatus.data.message,
        });
        setProgress({
          percent: resProgress.data?.percent ?? 0,
          task: resProgress.data?.task ?? "Idle",
        });
      }
    } catch (err) {
      console.error("Lỗi khi fetch dữ liệu hệ thống:", err);
      if (isMounted.current) {
        setStatus({
          type: "error",
          message: "Mất kết nối với máy chủ Backend",
        });
      }
    }
  }, []);

  useEffect(() => {
    isMounted.current = true;

    // Thay vì gọi trực tiếp fetchData(), ta đưa nó vào hàng đợi
    // của trình duyệt để tránh việc setState đồng bộ ngay lập tức
    const timeoutId = setTimeout(() => {
      fetchData();
    }, 0);

    const intervalId = setInterval(fetchData, 2000);

    // Cleanup function
    return () => {
      isMounted.current = false;
      clearTimeout(timeoutId);
      clearInterval(intervalId);
    };
  }, [fetchData]);

  return { status, progress };
};
