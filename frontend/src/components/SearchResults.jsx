// src/components/SearchResults.jsx
import React from "react";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import docco from "react-syntax-highlighter/dist/esm/styles/hljs/docco";

const SearchResults = ({ results }) => {
  if (!results) {
    return null;
  }

  if (results.length === 0) {
    return <p style={{ color: "gray" }}>No results found.</p>;
  }

  return (
    <div style={{ marginTop: "20px" }}>
      {results.map((item, index) => (
        <div
          key={index}
          style={{
            padding: "15px",
            marginBottom: "15px",
            border: "1px solid #ddd",
            borderRadius: "10px",
            backgroundColor: "#fff",
            boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
          }}
        >
          {/* Endpoint Path & Method */}
          {item.path && (
            <>
              <h3 style={{ margin: 0, color: "#2563eb" }}>
                {item.method} {item.path}
              </h3>
              <p style={{ margin: "5px 0", color: "#555" }}>
                {item.summary || "No description"}
              </p>
            </>
          )}

          {/* Component (if matched from components section) */}
          {item.component && (
            <>
              <h3 style={{ margin: 0, color: "#16a34a" }}>{item.component}</h3>
              <pre
                style={{
                  background: "#f9f9f9",
                  padding: "10px",
                  borderRadius: "5px",
                  overflowX: "auto",
                }}
              >
                {JSON.stringify(item.details, null, 2)}
              </pre>
            </>
          )}

          {/* Code Snippet */}
          {item.code_snippet && (
            <div style={{ marginTop: "10px" }}>
              <h4>Code Example:</h4>
              <SyntaxHighlighter language="python" style={docco} wrapLongLines>
                {item.code_snippet.replace(/```python|```/g, "").trim()}
              </SyntaxHighlighter>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default SearchResults;
