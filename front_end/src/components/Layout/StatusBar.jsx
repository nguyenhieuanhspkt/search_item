// Mảnh ghép này hiển thị trạng thái của AI (Đang nạp hay Sẵn sàng).

import { ShieldCheck, AlertCircle } from "lucide-react";
import { styles } from "../../constants/styles";

const StatusBar = ({ status }) => (
  <header style={{ ...styles.statusBar, ...styles[status.type] }}>
    {status.type === "ready" ? (
      <ShieldCheck size={20} />
    ) : (
      <AlertCircle size={20} />
    )}
    <span>{status.message}</span>
  </header>
);

export default StatusBar;
