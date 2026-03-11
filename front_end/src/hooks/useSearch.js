import { useState } from "react";
import axios from "axios";
import { API_BASE } from "../constants/config";

export const useSearch = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (statusType) => {
    if (!query || statusType !== "ready") return;
    setSearching(true);
    const formData = new FormData();
    formData.append("query", query);
    try {
      const res = await axios.post(`${API_BASE}/search`, formData);
      setResults(res.data);
    } catch {
      alert("Lỗi kết nối máy chủ tìm kiếm!");
    } finally {
      setSearching(false);
    }
  };

  return { query, setQuery, results, searching, handleSearch };
};
