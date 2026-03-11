import { useState } from "react";

export const useAuth = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [password, setPassword] = useState("");

  const login = (pass) => {
    if (pass === "admin123") {
      // Khớp với mật khẩu backend
      setIsAdmin(true);
      setPassword(pass);
      return true;
    }
    alert("Mật khẩu không đúng!");
    return false;
  };

  const logout = () => {
    setIsAdmin(false);
    setPassword("");
  };

  return { isAdmin, login, logout, adminPassword: password };
};
