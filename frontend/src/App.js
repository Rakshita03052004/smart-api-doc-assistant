import React, { useState, useEffect } from "react";
import Upload from "./components/upload";
import Summarize from "./components/summarize";
import Search from "./components/search";
import Chatbot from "./components/chatbot";

function App() {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoaded(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const containerStyle = {
    minHeight: "100vh",
    padding: "40px 20px",
    fontFamily: "'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    background: "#ffc42f",
    opacity: isLoaded ? 1 : 0,
    transform: isLoaded ? "translateY(0)" : "translateY(20px)",
    transition: "all 1s cubic-bezier(0.4, 0, 0.2, 1)",
    maxWidth: "1200px",
    margin: "0 auto"
  };

  const titleStyle = {
    fontSize: "clamp(2rem, 5vw, 3.5rem)",
    fontWeight: "700",
    color: "#2c2c2c",
    textAlign: "center",
    marginBottom: "60px",
    letterSpacing: "-0.02em",
    lineHeight: "1.2",
    opacity: isLoaded ? 1 : 0,
    transform: isLoaded ? "translateY(0)" : "translateY(30px)",
    transition: "all 1.2s cubic-bezier(0.4, 0, 0.2, 1) 0.2s"
  };

  return (
    <div style={{ minHeight: "100vh", padding: "20px", fontFamily: "Arial, sans-serif", background: "#ffc42f" }}>
      <div style={containerStyle}>
        <h1 style={titleStyle}>Smart API Documentation Assistant</h1>

        <section style={{ marginBottom: "20px" }}>
          <Summarize />
        </section>

        <section style={{ marginBottom: "20px" }}>
          <h2>3️⃣ Search API</h2>
          <Search />
        </section>

        <section style={{ marginBottom: "20px" }}>
          <h2>5️⃣ Chatbot</h2>
          <Chatbot />
        </section>
      </div>
    </div>
  );
}

export default App;
