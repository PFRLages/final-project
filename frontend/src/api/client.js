// src/api/client.js
import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Always make error.response.data.detail a STRING so pages never crash on it.
api.interceptors.response.use(
  (r) => r,
  (error) => {
    const d = error.response?.data?.detail;
    if (Array.isArray(d)) {
      error.response.data.detail = d.map((e) => e.msg || JSON.stringify(e)).join(", ");
    } else if (d && typeof d === "object") {
      error.response.data.detail = d.msg || JSON.stringify(d);
    }
    return Promise.reject(error);
  }
);

export default api;