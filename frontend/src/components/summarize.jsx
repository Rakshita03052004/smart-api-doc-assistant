import { useState } from "react";
import axios from "axios";

export default function Summarize() {
  const [summary, setSummary] = useState(null);

  const fetchSummary = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/summarize");
      setSummary(res.data);
    } catch (err) {
      console.error(err);
      setSummary("Failed to fetch summary");
    }
  };

  return (
    <div>
      <button onClick={fetchSummary}>Summarize API</button>
      <pre>{summary && JSON.stringify(summary, null, 2)}</pre>
    </div>
  );
}