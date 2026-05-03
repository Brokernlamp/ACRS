"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Send, Trash2, Loader2, Bot, User, AlertTriangle, CheckCircle } from "lucide-react";

interface Message {
  role: "user" | "model";
  content: string;
}

interface Status {
  gemini_configured: boolean;
  rag_documents_indexed: number;
  ready: boolean;
}

const SUGGESTIONS = [
  "Which campaign has the best ROI?",
  "What is the current CPL trend?",
  "Which campaign should I scale?",
  "Where is budget being wasted?",
  "What are the 7-day lead predictions?",
  "Which day of the week performs best?",
];

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "model",
      content:
        "Hi! I'm your AI marketing analyst. I have full context of your campaign data — ask me anything about performance, budgets, predictions, or recommendations.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.chatStatus().then(s => {
      setStatus(s as unknown as Status);
    }).catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const res = await api.chat(msg);
      setMessages((prev) => [...prev, { role: "model", content: res.reply }]);
      // Refresh status after first message (RAG may now be indexed)
      api.chatStatus().then(setStatus).catch(() => {});
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : "Failed to get response";
      setMessages((prev) => [...prev, { role: "model", content: `⚠️ ${err}` }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    await api.chatReset().catch(() => {});
    setMessages([
      { role: "model", content: "Conversation cleared. Ask me anything about your campaign data!" },
    ]);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Chatbot</h1>
          <p className="text-sm text-gray-500 mt-0.5">Ask questions about your campaign data in natural language</p>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 border border-gray-200 hover:border-red-300 px-3 py-1.5 rounded-lg transition-colors"
        >
          <Trash2 size={14} /> Clear chat
        </button>
      </div>

      {/* Status banners */}
      {status && !status.ready && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 rounded-lg mb-3">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <div className="space-y-1">
            {!status.rag_documents_indexed && (
              <p><strong>No data indexed.</strong> Upload a CSV on the Dashboard first.</p>
            )}
            {status.rag_documents_indexed > 0 && !(status as unknown as Record<string,unknown>)["ai_configured"] && (
              <p><strong>No AI key configured.</strong> Go to <strong>Settings</strong> and add a Groq or Gemini API key.</p>
            )}
          </div>
        </div>
      )}

      {status?.ready && (
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs px-4 py-2 rounded-lg mb-3">
          <CheckCircle size={13} />
          {status.rag_documents_indexed} documents indexed
          {" · "}
          {((status as unknown as Record<string,unknown>)["active_provider"] as string) !== "none"
            ? `${(status as unknown as Record<string,unknown>)["active_provider"]} connected`
            : "fallback mode"}
        </div>
      )}

      {/* Suggestions */}
      <div className="flex flex-wrap gap-2 mb-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => send(s)}
            disabled={loading}
            className="text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 px-3 py-1.5 rounded-full transition-colors disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 bg-white border border-gray-200 rounded-xl p-4 mb-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
            <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${m.role === "user" ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-600"}`}>
              {m.role === "user" ? <User size={15} /> : <Bot size={15} />}
            </div>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${m.role === "user" ? "bg-indigo-600 text-white rounded-tr-sm" : "bg-gray-100 text-gray-800 rounded-tl-sm"}`}>
              {m.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
              <Bot size={15} className="text-gray-600" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-gray-500" />
              <span className="text-sm text-gray-500">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask about your campaigns, budgets, predictions…"
          disabled={loading}
          className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50"
        />
        <button
          onClick={() => send()}
          disabled={loading || !input.trim()}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-3 rounded-xl transition-colors"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
