import axios from "axios";
import config from "../config/index.js";

const client = axios.create({
  baseURL: config.apiUrl,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Request interceptor — attach JWT token
client.interceptors.request.use(
  (reqConfig) => {
    const token = localStorage.getItem("devshort_token");
    if (token) {
      reqConfig.headers.Authorization = `Bearer ${token}`;
    }
    return reqConfig;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — unwrap data, handle errors
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const message = error.response.data?.error?.message || "An error occurred";

      // Auto-logout on 401
      if (error.response.status === 401) {
        localStorage.removeItem("devshort_token");
        // Only redirect if not already on login/register
        if (
          !window.location.pathname.includes("/login") &&
          !window.location.pathname.includes("/register")
        ) {
          window.location.href = "/login";
        }
      }

      return Promise.reject(new Error(message));
    }
    if (error.request) {
      return Promise.reject(new Error("Network error. Please check your connection."));
    }
    return Promise.reject(error);
  }
);

export default client;
