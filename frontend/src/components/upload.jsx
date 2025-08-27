// src/components/Upload.jsx
import { useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://127.0.0.1:8000/parse-spec", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setData(res.data); // full backend response
      setError("");
    } catch (err) {
      console.error(err);
      setError("❌ Upload failed");
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

      {/* Error */}
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {/* Response Preview */}
      {data && (
        <div className="mt-6 p-4 border rounded-lg bg-gray-50">
          <h2 className="font-bold text-lg mb-2">Spec Info</h2>
          <pre className="text-sm bg-white p-2 rounded">
            {JSON.stringify(data.info, null, 2)}
          </pre>

          <h2 className="font-bold text-lg mt-4 mb-2">Flow Diagram</h2>
          {data.flow && (
            <ReactMarkdown>
              {typeof data.flow === "string" ? data.flow : JSON.stringify(data.flow)}
            </ReactMarkdown>
          )}
        </div>
      )}
    </div>
  );
}
