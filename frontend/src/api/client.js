import axios from "axios";
import config from "../config/index.js";

const client = axios.create({
  baseURL: config.apiUrl,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const message = error.response.data?.error?.message || "An error occurred";
      return Promise.reject(new Error(message));
    }
    if (error.request) {
      return Promise.reject(new Error("Network error. Please check your connection."));
    }
    return Promise.reject(error);
  }
);

export default client;
