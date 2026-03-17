// src/components/Bulk/PreviewTable.jsx
import React from "react";
import { Table, Button, Space } from "antd";

// Dùng Named Export: export const ...
export const PreviewTable = ({ items, onConfirm, onCancel, loading }) => {
  // Định nghĩa các cột cho bảng Ant Design
  const columns = [
    {
      title: "STT",
      dataIndex: "stt",
      key: "stt",
      width: 70,
      align: "center",
    },
    {
      title: "Tên vật tư",
      dataIndex: "ten",
      key: "ten",
      render: (text) => <b>{text}</b>, // Làm đậm tên vật tư
    },
    {
      title: "Thông số kỹ thuật",
      dataIndex: "tskt",
      key: "tskt",
    },
    {
      title: "ĐVT",
      dataIndex: "dvt",
      key: "dvt",
      width: 80,
      align: "center",
    },
  ];

  return (
    <div style={{ marginTop: "20px" }}>
      <Table
        dataSource={items}
        columns={columns}
        bordered // <-- Dòng này để hiện gạch bảng dọc/ngang
        pagination={false} // Tắt phân trang vì đây là bản xem trước
        size="middle" // Kích thước bảng vừa phải
        rowKey={(record, index) => index} // Tránh lỗi thiếu key của Antd
      />

      <Space
        style={{
          marginTop: "16px",
          display: "flex",
          justifyContent: "flex-end",
        }}
      >
        <Button onClick={onCancel} danger>
          Hủy & Dán lại
        </Button>
        <Button type="primary" onClick={onConfirm} loading={loading}>
          Xác nhận đối soát AI
        </Button>
      </Space>
    </div>
  );
};
