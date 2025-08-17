import { useState } from "react";
import axios from "axios";

export default function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/search?query=${query}`);
      setResults(res.data.results);
    } catch (err) {
      console.error(err);
      setResults([]);
    }
  };

  return (
    <div>
      <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} />
      <button onClick={handleSearch}>Search</button>
      <pre>{results.length > 0 && JSON.stringify(results, null, 2)}</pre>
    </div>
  );
}