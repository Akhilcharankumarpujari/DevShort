import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import client from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem("devshort_token"));
  const [isLoading, setIsLoading] = useState(true);

  // Validate token on mount
  useEffect(() => {
    async function validateToken() {
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await client.get("/api/auth/me");
        setUser(response.data);
      } catch {
        localStorage.removeItem("devshort_token");
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    validateToken();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (email, password) => {
    const response = await client.post("/api/auth/login", { email, password });
    const { user: userData, token: newToken } = response.data;

    localStorage.setItem("devshort_token", newToken);
    setToken(newToken);
    setUser(userData);
    toast.success(`Welcome back, ${userData.name}!`);
    return userData;
  }, []);

  const register = useCallback(async (name, email, password) => {
    const response = await client.post("/api/auth/register", { name, email, password });
    const { user: userData, token: newToken } = response.data;

    localStorage.setItem("devshort_token", newToken);
    setToken(newToken);
    setUser(userData);
    toast.success("Account created successfully!");
    return userData;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("devshort_token");
    setToken(null);
    setUser(null);
    toast.success("Logged out successfully");
  }, []);

  const value = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export default AuthContext;
