import { useState } from "react";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const ask = async () => {
    if (!input) return;

    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);

    const res = await fetch("http://localhost:7071/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: input }),
    });

    const data = await res.json();

    const botMsg = {
      role: "bot",
      text: data.answer || "No response",
    };

    setMessages((prev) => [...prev, botMsg]);
    setInput("");
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">

      {/* Sidebar */}
      <div className="w-64 bg-gray-800 p-4 border-r border-gray-700">
        <h2 className="text-lg font-bold mb-4">💬 Chats</h2>
        <button className="w-full bg-blue-600 p-2 rounded hover:bg-blue-700">
          + New Chat
        </button>

        <div className="mt-4 space-y-2 text-sm text-gray-300">
          <p className="truncate">Policy Questions</p>
          <p className="truncate">Land Details</p>
        </div>
      </div>

      {/* Main Chat */}
      <div className="flex flex-col flex-1">

        {/* Header */}
        <div className="p-4 border-b border-gray-700 text-xl font-semibold">
          🏠 Real Estate AI Assistant
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`max-w-xl p-3 rounded-lg ${
                msg.role === "user"
                  ? "bg-blue-500 ml-auto"
                  : "bg-gray-700 mr-auto"
              }`}
            >
              {msg.text}
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-700 flex gap-2">
          <input
            className="flex-1 p-3 rounded bg-gray-800 outline-none"
            placeholder="Ask about your document..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
          />
          <button
            onClick={ask}
            className="bg-blue-600 px-6 rounded hover:bg-blue-700"
          >
            Send
          </button>
        </div>

      </div>
    </div>
  );
}

export default App;