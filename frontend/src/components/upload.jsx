// src/components/Upload.jsx
import { useState } from "react";
import axios from "axios";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://127.0.0.1:8000/parse-spec", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMessage(res.data.message || "Spec uploaded successfully");
    } catch (err) {
      console.error(err);
      setMessage("❌ Upload failed");
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* File Upload */}
      <input
        type="file"
        accept=".json,.yaml,.yml"
        onChange={(e) => setFile(e.target.files[0])}
        className="mb-4 block w-full border p-2 rounded-lg"
      />

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        className="px-4 py-2 bg-green-600 text-white rounded-lg shadow hover:bg-green-700"
      >
        Upload Spec
      </button>

      {/* Status Message */}
      {message && <p className="mt-3 text-sm">{message}</p>}
    </div>
  );
}