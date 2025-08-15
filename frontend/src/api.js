import axios from "axios";

// Backend URL (FastAPI)
const API_BASE = "http://127.0.0.1:8000";

// Upload API Spec
export const uploadSpec = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return axios.post(`${API_BASE}/upload-spec`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
};

// Ask a question about the API
export const askQuestion = (question) => {
  return axios.post(`${API_BASE}/ask`, { question });
};

// Get generated documentation
export const getDocs = () => {
  return axios.get(`${API_BASE}/docs-data`);
};
