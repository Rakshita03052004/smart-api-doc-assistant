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
      setData(res.data);
      setError("");
    } catch (err) {
      console.error(err);
      setError("❌ Upload failed");
    }
  };

  const cardStyle = {
    backgroundColor: "rgba(255, 255, 255, 0.95)",
    borderRadius: "20px",
    padding: "40px",
    boxShadow: "0 15px 50px rgba(0,0,0,0.2)",
    backdropFilter: "blur(15px)",
    border: "1px solid rgba(255,255,255,0.3)",
    maxWidth: "800px",
    margin: "0 auto",
    textAlign: "center",
  };

  const inputStyle = {
    width: "100%",
    padding: "18px",
    fontSize: "18px",
    borderRadius: "12px",
    border: "2px solid #2c2c2c",
    marginBottom: "20px",
    cursor: "pointer",
  };

  const buttonStyle = {
    padding: "18px 36px",
    fontSize: "20px",
    borderRadius: "12px",
    backgroundColor: "#2c2c2c",
    color: "white",
    border: "none",
    cursor: "pointer",
    boxShadow: "0 8px 20px rgba(0,0,0,0.15)",
    transition: "all 0.3s ease",
  };

  const buttonHoverStyle = {
    backgroundColor: "#444",
    transform: "translateY(-3px) scale(1.02)",
    boxShadow: "0 12px 25px rgba(0,0,0,0.2)",
  };

  const [isHover, setIsHover] = useState(false);

  return (
    <div style={cardStyle}>
      <h2 style={{ fontSize: "2rem", fontWeight: "700", marginBottom: "30px", color: "#2c2c2c" }}>
        Upload API Spec
      </h2>

      {/* File Input */}
      <input
        type="file"
        accept=".json,.yaml,.yml"
        onChange={(e) => setFile(e.target.files[0])}
        style={inputStyle}
      />

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        style={{ ...buttonStyle, ...(isHover ? buttonHoverStyle : {}) }}
        onMouseEnter={() => setIsHover(true)}
        onMouseLeave={() => setIsHover(false)}
      >
        Upload & Parse
      </button>

      {/* Error */}
      {error && <p style={{ marginTop: "20px", color: "red", fontSize: "1rem" }}>{error}</p>}

      {/* Response Preview */}
      {data && (
        <div style={{
          marginTop: "40px",
          textAlign: "left",
          padding: "25px",
          borderRadius: "16px",
          backgroundColor: "#f9f9f9",
          boxShadow: "0 5px 25px rgba(0,0,0,0.1)"
        }}>
          <h3 style={{ fontWeight: "600", marginBottom: "15px" }}>Spec Info</h3>
          <pre style={{
            backgroundColor: "#fff",
            padding: "20px",
            borderRadius: "12px",
            overflowX: "auto",
            fontSize: "1rem"
          }}>
            {JSON.stringify(data.info, null, 2)}
          </pre>

          {data.flow && (
            <>
              <h3 style={{ fontWeight: "600", marginTop: "30px", marginBottom: "15px" }}>Flow Diagram</h3>
              <ReactMarkdown style={{ fontSize: "1rem" }}>
                {typeof data.flow === "string" ? data.flow : JSON.stringify(data.flow)}
              </ReactMarkdown>
            </>
          )}
        </div>
      )}
    </div>
  );
}
