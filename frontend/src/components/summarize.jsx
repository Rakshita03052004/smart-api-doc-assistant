// src/components/Summarize.jsx
import { useState, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import mermaid from "mermaid";

export default function Summarize() {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const res = await axios.get("http://127.0.0.1:8000/api-summary", {
        headers: { Accept: "text/markdown, text/plain, text/html" },
      });
      setSummary(typeof res.data === "string" ? res.data : String(res.data));
    } catch (err) {
      console.error(err);
      setSummary("❌ Failed to fetch summary");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (summary) mermaid.init();
  }, [summary]);

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <button
        onClick={fetchSummary}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "⏳ Working..." : "Summarize API"}
      </button>

      {summary && (
        <div className="mt-6 p-4 border rounded-lg shadow bg-white prose">
          <h2 className="text-xl font-semibold mb-2">✨ API Summary</h2>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {summary}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}