import { useState } from "react";
import axios from "axios";

export default function Examples() {
  const [examples, setExamples] = useState(null);

  const fetchExamples = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/examples");
      setExamples(res.data);
    } catch (err) {
      console.error(err);
      setExamples("Failed to fetch examples");
    }
  };

  return (
    <div>
      <button onClick={fetchExamples}>Get Examples</button>
      <pre>{examples && JSON.stringify(examples, null, 2)}</pre>
    </div>
  );
}