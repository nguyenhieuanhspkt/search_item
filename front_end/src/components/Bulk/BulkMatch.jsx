// src/components/Bulk/BulkMatch.jsx
import React, { useState } from "react";
import { Layout, Typography, Card, message } from "antd"; // Thêm message để báo lỗi cho chuyên nghiệp
import { processPasteData, sendMatchRequest } from "./bulkUtils";

// 1. IMPORT TAG: Dùng ngoặc nhọn vì bên PreviewTable dùng "export const"
import { PreviewTable } from "./PreviewTable";

const { Content } = Layout;
const { Title } = Typography;

const BulkMatch = () => {
  const [items, setItems] = useState([]); // Dữ liệu thô sau khi dán
  const [results, setResults] = useState([]); // Dữ liệu AI trả về
  const [loading, setLoading] = useState(false);

  // 2. XỬ LÝ DÁN DỮ LIỆU
  const handlePaste = (e) => {
    const rawText = e.clipboardData.getData("text");
    if (!rawText) return;

    const formattedData = processPasteData(rawText);
    if (formattedData.length > 0) {
      setItems(formattedData);
      setResults([]); // Reset kết quả cũ nếu dán bộ mới
      message.success(`Đã nhận diện ${formattedData.length} dòng vật tư`);
    } else {
      message.error("Dữ liệu dán vào không đúng định dạng bảng!");
    }
  };

  // 3. XỬ LÝ KHI BẤM NÚT XÁC NHẬN TRÊN BẢNG PREVIEW
  const handleConfirmAI = async () => {
    setLoading(true);
    try {
      const res = await sendMatchRequest(items);
      if (res.success) {
        setResults(res.data);
        message.success("Đối soát AI hoàn tất!");
      } else {
        message.error(res.message || "Lỗi khi gọi AI");
      }
    } catch (err) {
      message.error("Lỗi hệ thống:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout
      style={{ padding: "24px", minHeight: "100vh", background: "#f0f2f5" }}
    >
      <Content style={{ maxWidth: 1200, margin: "0 auto", width: "100%" }}>
        <Card
          bordered={false}
          style={{
            borderRadius: "12px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
          }}
        >
          <Title
            level={2}
            style={{ textAlign: "center", marginBottom: "32px" }}
          >
            HỆ THỐNG ĐỐI SOÁT VẬT TƯ AIIII
          </Title>

          {/* GIAI ĐOẠN 1: NẾU CHƯA CÓ DỮ LIỆU -> HIỆN Ô DÁN (DASHED BOX) */}
          {items.length === 0 ? (
            <div
              onPaste={handlePaste}
              style={{
                padding: "100px 20px",
                border: "2px dashed #1890ff",
                background: "#e6f7ff",
                textAlign: "center",
                borderRadius: "12px",
                cursor: "pointer",
                transition: "all 0.3s",
              }}
            >
              <p
                style={{
                  fontSize: "18px",
                  color: "#1890ff",
                  fontWeight: "bold",
                }}
              >
                Click vào đây và nhấn Ctrl + V để dán bảng từ Word/Excel
              </p>
              <p style={{ color: "#8c8c8c" }}>
                Hệ thống sẽ tự động tách STT, Tên, TSKT, ĐVT
              </p>
            </div>
          ) : (
            /* GIAI ĐOẠN 2: NẾU ĐÃ CÓ DỮ LIỆU -> HIỆN TAG PREVIEW TABLE */
            /* results.length === 0 nghĩa là chưa bấm AI, chỉ đang xem trước */
            results.length === 0 && (
              <PreviewTable
                items={items}
                onConfirm={handleConfirmAI} // Truyền hàm xử lý AI xuống tag
                onCancel={() => setItems([])} // Truyền hàm xóa dữ liệu xuống tag
                loading={loading}
              />
            )
          )}

          {/* GIAI ĐOẠN 3: HIỆN KẾT QUẢ SAU KHI AI XỬ LÝ XONG */}
          {results.length > 0 && (
            <div style={{ marginTop: "40px" }}>
              <Title level={4} style={{ color: "#52c41a" }}>
                ✓ KẾT QUẢ ĐỐI SOÁT CHI TIẾT
              </Title>
              {/* Ở đây ông có thể dùng ResultTable của ông hoặc viết table kết quả tại đây */}
              <p>Đã tìm thấy {results.length} mã tương ứng trong kho.</p>
              <button
                onClick={() => {
                  setItems([]);
                  setResults([]);
                }}
                style={{ color: "red" }}
              >
                Làm mẻ mới
              </button>
            </div>
          )}
        </Card>
      </Content>
    </Layout>
  );
};

export default BulkMatch;
