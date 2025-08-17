// src/App.js
import React from "react";
import Upload from "./components/upload";
import Summarize from "./components/summarize";
import Search from "./components/search";
import Examples from "./components/examples";
import Chatbot from "./components/chatbot";

function App() {
  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>Smart API Documentation Assistant</h1>

      <section style={{ marginBottom: "20px" }}>
        <h2>1️⃣ Upload API Spec</h2>
        <Upload />
      </section>

      <section style={{ marginBottom: "20px" }}>
        <h2>2️⃣ Summarize API</h2>
        <Summarize />
      </section>

      <section style={{ marginBottom: "20px" }}>
        <h2>3️⃣ Search API</h2>
        <Search />
      </section>

      <section style={{ marginBottom: "20px" }}>
        <h2>4️⃣ API Examples</h2>
        <Examples />
      </section>

      <section style={{ marginBottom: "20px" }}>
        <h2>5️⃣ Chatbot</h2>
        <Chatbot />
      </section>
    </div>
  );
}

export default App;