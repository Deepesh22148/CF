"use client";

import React from "react";
import PersonalLayout from "@/components/layout/PersonalLayout";

type Message = {
  id: string;
  text: string;
  createdAt: number;
};

const ChatApplicationPage = ({ user_id }: { user_id: string }) => {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState("");

  const bottomRef = React.useRef<HTMLDivElement | null>(null);

  const sendMessage = () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        text: trimmed,
        createdAt: Date.now(),
      },
    ]);

    setInput("");
  };

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <PersonalLayout user_id={user_id}>

      <div className="h-full flex flex-col bg-slate-900 text-slate-200">

        <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-3 bg-slate-900">

          {messages.map((msg) => (
            <div
              key={msg.id}
              className="bg-slate-800 border border-slate-700 text-slate-100 px-3 py-2 rounded-lg w-fit max-w-[70%] wrap-break-word"
            >
              {msg.text}
            </div>
          ))}

          <div ref={bottomRef} />
        </div>

        <div className="shrink-0 border-t border-slate-700 bg-slate-900 px-4 py-3">
          <div className="flex gap-2">

            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") sendMessage();
              }}
              placeholder="Type a message..."
              className="flex-1 bg-slate-800 border border-slate-600 text-slate-100 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-cyan-400"
            />

            <button
              onClick={sendMessage}
              className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-medium px-4 py-2 rounded-lg transition"
            >
              Send
            </button>

          </div>
        </div>

      </div>

    </PersonalLayout>
  );
};

export default ChatApplicationPage;