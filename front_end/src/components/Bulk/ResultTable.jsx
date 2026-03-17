import React from "react";
import { Table, Button, Tag, Progress, Typography, Card } from "antd";
import { DownloadOutlined, FileTextOutlined } from "@ant-design/icons";

const { Text } = Typography;

const ResultTable = ({ results, onExport }) => {
  const columns = [
    {
      title: "STT",
      dataIndex: "stt",
      key: "stt",
      width: 60,
      align: "center",
    },
    {
      title: "Vật tư gốc",
      key: "word_name",
      width: "30%",
      render: (res) => (
        <div>
          <div style={{ fontWeight: "bold", textTransform: "uppercase" }}>
            {res.word_name}
          </div>
          <Text type="secondary" style={{ fontSize: "11px" }}>
            {res.full_stock_info?.ts_goc}
          </Text>
        </div>
      ),
    },
    {
      title: "Gợi ý từ kho (AI)",
      key: "match",
      render: (res) => (
        <div>
          <div
            style={{ marginBottom: 8, fontSize: "13px" }}
            dangerouslySetInnerHTML={{ __html: res.diff_html }}
          />
          <Space size={[0, 4]} wrap>
            <Tag color="blue">MÃ: {res.full_stock_info?.ma}</Tag>
            <Tag color="cyan">ĐVT: {res.full_stock_info?.dvt}</Tag>
          </Space>
        </div>
      ),
    },
    {
      title: "Độ tin cậy",
      dataIndex: "score",
      key: "score",
      width: 120,
      align: "center",
      render: (score) => (
        <Progress
          type="circle"
          percent={(score * 100).toFixed(0)}
          size={40}
          strokeColor={
            score > 0.8 ? "#52c41a" : score > 0.5 ? "#faad14" : "#ff4d4f"
          }
        />
      ),
    },
  ];

  return (
    <Card
      title={
        <Space>
          <FileTextOutlined />
          <span>KẾT QUẢ ĐỐI SOÁT</span>
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<DownloadOutlined />}
          onClick={onExport}
          color="success"
          variant="solid"
        >
          XUẤT EXCEL
        </Button>
      }
      style={{ marginTop: 24 }}
    >
      <Table
        dataSource={results}
        columns={columns}
        rowKey={(record, index) => index}
        bordered
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};

export default ResultTable;
