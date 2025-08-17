import { useState } from "react";
import axios from "axios";

export default function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", text: input };
    setMessages([...messages, userMessage]);
    setInput("");

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        message: input,
      });

      const botMessage = {
        role: "bot",
        text: res.data.answer,
        code: res.data.code_snippet,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ width: "400px", margin: "20px auto", border: "1px solid #ccc", padding: "10px", borderRadius: "8px" }}>
      <div style={{ maxHeight: "300px", overflowY: "auto", marginBottom: "10px" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ textAlign: msg.role === "user" ? "right" : "left", margin: "5px 0" }}>
            <div style={{ display: "inline-block", padding: "8px", borderRadius: "5px", backgroundColor: msg.role === "user" ? "#007bff" : "#f1f1f1", color: msg.role === "user" ? "#fff" : "#000" }}>
              {msg.text}
            </div>
            {msg.code && (
              <pre style={{ backgroundColor: "#eee", padding: "5px", marginTop: "5px" }}>
                {JSON.stringify(msg.code, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>

      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        style={{ width: "80%", padding: "5px" }}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
      />
      <button onClick={sendMessage} style={{ width: "18%", marginLeft: "2%", padding: "5px" }}>Send</button>
    </div>
  );
}