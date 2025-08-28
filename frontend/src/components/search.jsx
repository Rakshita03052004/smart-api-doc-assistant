import React, { useState } from "react";
import axios from "axios";

const Search = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    try {
      setError("");
      const res = await axios.get("http://localhost:8000/search", {
        params: { keyword: query },
      });
      if (res.data.results) {
        setResults(res.data.results);
      } else if (res.data.message) {
        setResults([]);
        setError(res.data.message);
      }
    } catch (err) {
      console.error(err);
      setError("Error fetching results");
    }
  };

  return (
    <div>
      <h3>🔍 Search API</h3>
      <input
        type="text"
        value={query}
        placeholder="Search endpoints..."
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div>
        {results.length > 0 ? (
          <table border="1" cellPadding="6">
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Method</th>
                <th>Summary</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {results.map((item, idx) => (
                <tr key={idx}>
                  <td>{item.endpoint}</td>
                  <td>{item.method}</td>
                  <td>{item.summary}</td>
                  <td>{item.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          query && !error && <p>No results found</p>
        )}
      </div>
    </div>
  );
};

export default Search;
