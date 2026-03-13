import React, { useState } from "react";
import axios from "axios";
import { API_BASE } from "../../constants/config";
import * as XLSX from "xlsx";

const BulkMatch = () => {
  const [items, setItems] = useState([]); // Dữ liệu dán từ Word
  const [results, setResults] = useState([]); // Kết quả AI trả về
  const [loading, setLoading] = useState(false);

  // --- PHÂN TRANG ---
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  // 1. XỬ LÝ DÁN BẢNG (PASTE)
  const handlePaste = (e) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData("text");
    if (!pasteData) return;

    const rows = pasteData.split("\n").filter((row) => row.trim() !== "");
    const formatted = rows.map((row, index) => {
      const cells = row.split("\t"); // Tách cột theo phím Tab của Word/Excel
      return {
        stt: cells[0] || index + 1,
        ten: cells[1] || "Trống tên",
        tskt: cells[2] || "",
        dvt: cells[3] || "",
      };
    });

    setItems(formatted);
    setResults([]); // Reset kết quả cũ
    setCurrentPage(1);
  };

  // 2. GỌI API ĐỐI SOÁT
  const startMatching = async () => {
    if (items.length === 0) return;
    setLoading(true);
    try {
      // Dùng API_BASE_URL từ file config.js của ông
      const response = await axios.post(`${API_BASE}/api/bulk-match`, items);
      setResults(response.data.data);
    } catch (error) {
      console.error("Lỗi đối soát:", error);
      alert("Không thể kết nối Backend AI. Hãy kiểm tra server!");
    } finally {
      setLoading(false);
    }
  };

  // 3. XỬ LÝ XUẤT EXCEL
  const exportExcel = () => {
    const data = results.map((res) => ({
      STT: res.stt,
      "Tên (Word)": res.word_item.ten,
      "TSKT (Word)": res.word_item.tskt,
      "Vật tư khớp nhất (Kho)": res.stock_item?.ten || "N/A",
      "Mã kho": res.stock_item?.ma || "",
      "Độ tin cậy": (res.score * 100).toFixed(0) + "%",
    }));
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "DoiSoat");
    XLSX.writeFile(wb, "Ket_qua_doi_soat_AI.xlsx");
  };

  // 4. LOGIC PHÂN TRANG
  const totalPages = Math.ceil(results.length / rowsPerPage);
  const currentData = results.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage,
  );

  return (
    <div className="flex flex-col gap-6 p-4 max-w-6xl mx-auto font-sans">
      {/* VÙNG NHẬP LIỆU */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 uppercase tracking-tight">
          Đối soát danh mục hàng loạt
        </h2>

        {items.length === 0 ? (
          <div
            onPaste={handlePaste}
            className="border-2 border-dashed border-blue-200 bg-blue-50 h-40 flex flex-col items-center justify-center rounded-xl cursor-pointer hover:bg-blue-100 transition-all group"
          >
            <div className="text-blue-500 mb-2 group-hover:scale-110 transition-transform">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-10 w-10"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
            </div>
            <p className="text-blue-700 font-semibold">
              Nhấp vào đây rồi nhấn Ctrl + V để dán bảng Word
            </p>
            <p className="text-gray-400 text-xs mt-1">
              Hệ thống tự nhận diện các cột STT | Tên | TSKT | ĐVT
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex justify-between items-center bg-green-50 p-3 rounded-lg border border-green-200">
              <span className="text-green-700 font-medium">
                ✓ Đã nạp <b>{items.length}</b> dòng từ clipboard
              </span>
              <button
                onClick={() => setItems([])}
                className="text-red-500 text-xs hover:underline"
              >
                Xóa làm lại
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={startMatching}
                disabled={loading}
                className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700 disabled:bg-gray-400 transition-all shadow-lg"
              >
                {loading ? "AI ĐANG XỬ LÝ..." : "BẮT ĐẦU ĐỐI SOÁT BẰNG AI"}
              </button>
              {results.length > 0 && (
                <button
                  onClick={exportExcel}
                  className="bg-green-600 text-white px-6 rounded-lg font-bold hover:bg-green-700 shadow-md"
                >
                  Xuất Excel
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* BẢNG KẾT QUẢ */}
      {results.length > 0 && (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-4 w-12 text-center text-gray-500">STT</th>
                <th className="p-4 text-left font-semibold">Vật tư (Word)</th>
                <th className="p-4 text-left font-semibold">
                  Gợi ý khớp nhất (Kho)
                </th>
                <th className="p-4 text-center font-semibold">Độ tin cậy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {currentData.map((res, i) => (
                <tr key={i} className="hover:bg-blue-50/50 transition-colors">
                  <td className="p-4 text-center text-gray-400 font-mono">
                    {res.stt}
                  </td>
                  <td className="p-4">
                    <div className="font-bold text-gray-800 uppercase text-[13px]">
                      {res.word_item.ten}
                    </div>
                    <div className="text-gray-500 text-[11px] italic">
                      {res.word_item.tskt}
                    </div>
                  </td>
                  <td className="p-4 border-l border-gray-50">
                    {/* Render diff_html với màu sắc từ Backend */}
                    <div
                      className="text-[13px] leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: res.diff_html }}
                    />
                    <div className="text-[10px] text-blue-500 font-mono mt-1">
                      CODE: {res.stock_item?.ma || "KHÔNG CÓ MÃ"}
                    </div>
                  </td>
                  <td className="p-4 text-center">
                    <div
                      className={`inline-block px-3 py-1 rounded-full font-black text-[12px] ${
                        res.score > 0.8
                          ? "bg-green-100 text-green-700"
                          : res.score > 0.5
                            ? "bg-orange-100 text-orange-700"
                            : "bg-red-100 text-red-700"
                      }`}
                    >
                      {(res.score * 100).toFixed(0)}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* THANH PHÂN TRANG */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 p-4 border-t bg-gray-50">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
                className="px-4 py-1 text-sm border rounded bg-white hover:bg-gray-100 disabled:opacity-30"
              >
                Trang trước
              </button>
              <span className="text-sm font-bold text-gray-600">
                Trang {currentPage} / {totalPages}
              </span>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
                className="px-4 py-1 text-sm border rounded bg-white hover:bg-gray-100 disabled:opacity-30"
              >
                Trang sau
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BulkMatch;
