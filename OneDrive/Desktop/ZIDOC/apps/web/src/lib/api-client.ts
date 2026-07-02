import axios from "axios"

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
})

// Automatically append X-Request-ID for distributed tracing
apiClient.interceptors.request.use((config) => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    config.headers["X-Request-ID"] = crypto.randomUUID()
  } else {
    // Fallback simple ID generator if crypto is not fully accessible
    config.headers["X-Request-ID"] = Math.random().toString(36).substring(2, 15)
  }
  return config
})

export default apiClient
