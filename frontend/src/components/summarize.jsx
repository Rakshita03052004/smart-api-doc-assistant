import { useState, useEffect, useMemo, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import mermaid from "mermaid";

// ---- Simple Tabs ----
function Tabs({ tabs, value, onChange }) {
  return (
    <div className="w-full mb-4">
      <div className="flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.value}
            onClick={() => onChange(t.value)}
            className={`px-3 py-1.5 rounded-lg border shadow-sm text-sm transition
              ${
                value === t.value
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white hover:bg-gray-100 border-gray-300"
              }`}
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function Summarize() {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("overview");

  const [file, setFile] = useState(null);
  const [uploadInfo, setUploadInfo] = useState("");
  const flowRef = useRef(null);

  // ---- Upload OpenAPI spec ----
  const uploadSpec = async () => {
    if (!file) return alert("Choose a JSON/YAML spec first.");
    const form = new FormData();
    form.append("file", file);
    try {
      setUploadInfo("⏳ Uploading...");
      const res = await fetch("http://127.0.0.1:8000/upload-spec", {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setUploadInfo(
        `✅ Uploaded: ${data.title} (v${data.version}) — ${data.path_count} paths`
      );
    } catch (e) {
      setUploadInfo("❌ Upload failed: " + e.message);
    }
  };

  // ---- Fetch summary ----
  const fetchSummary = async () => {
    if (!file) return alert("Upload a spec first!");
    try {
      setLoading(true);
      const res = await axios.get("http://127.0.0.1:8000/api-summary", {
        headers: { Accept: "text/markdown, text/plain" },
      });
      setSummary(typeof res.data === "string" ? res.data : String(res.data));
    } catch (err) {
      console.error(err);
      setSummary("❌ Failed to fetch summary");
    } finally {
      setLoading(false);
    }
  };

  // ---- Extract sections ----
  const sections = useMemo(() => {
    const s = summary || "";
    const endpointsMatch = s.match(/### Endpoints:[\s\S]*?(?=(\n### |\n## )|$)/);
    const paramsMatch = s.match(/### Parameters:[\s\S]*?(?=(\n### |\n## )|$)/);
    const authMatch = s.match(/## 🔐[\s\S]*?(?=(\n## )|$)/);
    const flowMatch = s.match(/```mermaid([\s\S]*?)```/);

    let overview = s;
    const firstBreak = Math.min(
      ...[endpointsMatch?.index, authMatch?.index].filter((x) => x !== undefined)
    );
    if (Number.isFinite(firstBreak)) overview = s.slice(0, firstBreak);

    const flowCode = flowMatch ? flowMatch[1].trim() : "";

    return {
      overview,
      endpoints: endpointsMatch ? endpointsMatch[0] : "",
      params: paramsMatch ? paramsMatch[0] : "",
      auth: authMatch ? authMatch[0] : "",
      flow: flowCode,
    };
  }, [summary]);

  // ---- Render Mermaid when flow tab is active ----
  useEffect(() => {
    if (tab === "flow" && sections.flow && flowRef.current) {
      try {
        mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });
        flowRef.current.innerHTML = "";
        mermaid.render("apiFlow", sections.flow, (svgCode) => {
          flowRef.current.innerHTML = svgCode;
        });
      } catch (e) {
        console.warn("Mermaid render failed:", e);
      }
    }
  }, [tab, sections.flow]);

  const tabs = [
    { value: "overview", label: "📄 Overview" },
    { value: "endpoints", label: "🔗 Endpoints" },
    { value: "params", label: "⚙️ Parameters" },
    { value: "auth", label: "🔐 Auth" },
    { value: "flow", label: "🔄 Flow" },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold">🧠 Summarize API</h1>
        <div className="flex gap-2 items-center">
          <input
            type="file"
            accept=".json,.yaml,.yml"
            onChange={(e) => setFile(e.target.files[0])}
            className="text-sm"
          />
          <button
            onClick={uploadSpec}
            className="px-3 py-2 bg-gray-200 rounded hover:bg-gray-300"
          >
            Upload Spec
          </button>
          <button
            onClick={fetchSummary}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "⏳ Working..." : "Summarize API"}
          </button>
        </div>
      </div>

      {uploadInfo && <p className="text-gray-600 mt-2">{uploadInfo}</p>}

      {!summary && (
        <p className="text-gray-600 mt-4">
          1) Upload a spec → 2) Click <b>Summarize API</b> to generate overview,
          tables, and a Mermaid flow diagram.
        </p>
      )}

      {summary && (
        <div className="mt-6 p-6 rounded-xl shadow bg-white">
          <Tabs tabs={tabs} value={tab} onChange={setTab} />
          <div className="prose max-w-none mt-4">
            {tab === "overview" && <ReactMarkdown remarkPlugins={[remarkGfm]}>{sections.overview}</ReactMarkdown>}
            {tab === "endpoints" && <EndpointsTable markdown={sections.endpoints} />}

            {tab === "params" && <ParametersTable markdown={sections.params} />}

            {tab === "auth" && <ReactMarkdown remarkPlugins={[remarkGfm]}>{sections.auth}</ReactMarkdown>}
            {tab === "flow" && <div ref={flowRef} className="w-full overflow-x-auto" />}
          </div>
        </div>
      )}
    </div>
  );
}
function EndpointsTable({ markdown }) {
  const rows = markdown
    .split("\n")
    .filter((line) => line.startsWith("|"))
    .map((line) =>
      line
        .split("|")
        .map((c) => c.trim())
        .filter((c) => c)
    );

  if (rows.length < 2) return <p>No endpoints found.</p>;

  const headers = rows[0];
  const data = rows.slice(1);

  return (
    <div className="overflow-x-auto">
      <table className="table-auto w-full border border-gray-300 rounded-lg shadow-sm">
        <thead className="bg-green-400 text-black">
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="px-3 py-2 text-left text-sm font-bold border">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((cols, rowIdx) => (
            <tr key={rowIdx} className="odd:bg-white even:bg-gray-50">
              {cols.map((col, colIdx) => (
                <td key={colIdx} className="px-3 py-2 text-sm border text-gray-800">
                  {col}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ParametersTable({ markdown }) {
  // Extract rows from markdown (| col | col | col | style tables)
  const rows = markdown
    .split("\n")
    .filter((line) => line.startsWith("|"))
    .map((line) =>
      line
        .split("|")
        .map((c) => c.trim())
        .filter((c) => c)
    );

  if (rows.length < 2) return <p>No parameters found.</p>;

  const headers = rows[0];
  const data = rows.slice(1);

  return (
    <div className="overflow-x-auto">
      <table className="table-auto w-full border border-gray-300 rounded-lg shadow-sm">
        <thead className="bg-yellow-400 text-black">
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="px-3 py-2 text-left text-sm font-bold border">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((cols, rowIdx) => (
            <tr key={rowIdx} className="odd:bg-white even:bg-gray-50">
              {cols.map((col, colIdx) => (
                <td
                  key={colIdx}
                  className="px-3 py-2 text-sm border text-gray-800"
                >
                  {col === "❌" ? (
                    <span className="text-red-500 font-bold">✘</span>
                  ) : col === "✅" ? (
                    <span className="text-green-600 font-bold">✔</span>
                  ) : (
                    col
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
