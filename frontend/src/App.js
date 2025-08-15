import React, { useState } from "react";
import { uploadSpec, askQuestion, getDocs } from "./api";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [docs, setDocs] = useState([]);
  const [file, setFile] = useState(null);

  const handleUpload = () => {
    if (!file) return alert("Please select a file first");
    uploadSpec(file)
      .then((res) => alert(`✅ File uploaded: ${res.data.filename}`))
      .catch((err) => console.error(err));
  };

  const handleAsk = () => {
    if (!question.trim()) return alert("Please enter a question");
    askQuestion(question)
      .then((res) => setAnswer(res.data.answer))
      .catch((err) => console.error(err));
  };

  const handleGetDocs = () => {
    getDocs()
      .then((res) => setDocs(res.data))
      .catch((err) => console.error(err));
  };

  return (
    <div className="app-container">
      <h1>⚡ API Backend Tester</h1>

      {/* Upload Section */}
      <div className="card">
        <h3>📄 Upload API Spec</h3>
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        <button className="button" onClick={handleUpload}>
          Upload
        </button>
      </div>

      {/* Ask Question Section */}
      <div className="card">
        <h3>❓ Ask Backend a Question</h3>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question here"
        />
        <button className="button" onClick={handleAsk}>
          Ask
        </button>
        {answer && (
          <p style={{ marginTop: "10px", color: "#4f46e5" }}>
            <b>Answer:</b> {answer}
          </p>
        )}
      </div>

      {/* Get Docs Section */}
      <div className="card">
        <h3>📚 Get API Docs</h3>
        <button className="button" onClick={handleGetDocs}>
          Fetch Docs
        </button>
        {docs.length > 0 && (
          <ul>
            {docs.map((doc, i) => (
              <li key={i}>
                <b>{doc.method}</b> {doc.path} - {doc.description}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default App;
