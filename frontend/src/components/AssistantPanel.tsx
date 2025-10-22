import { MicrophoneIcon, PaperAirplaneIcon } from "@heroicons/react/24/solid";
import React, { useCallback, useRef, useState } from "react";
import { useApi } from "../hooks/useApi";

interface AssistantMessage {
  role: "user" | "assistant";
  content: string;
}

interface AssistantPanelProps {
  videoId: number;
}

const AssistantPanel: React.FC<AssistantPanelProps> = ({ videoId }) => {
  const api = useApi();
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

  const ensureSession = useCallback(async () => {
    if (sessionIdRef.current) {
      return sessionIdRef.current;
    }
    const response = await api.post<{ session_id: string }>("/chat/sessions", null, {
      params: { video_id: videoId }
    });
    sessionIdRef.current = response.data.session_id ?? null;
    return sessionIdRef.current;
  }, [api, videoId]);

  const sendQuestion = useCallback(
    async (question: string) => {
      setLoading(true);
      try {
        const sessionId = await ensureSession();
        const response = await api.post("/chat/query", {
          video_id: videoId,
          question,
          session_id: sessionId
        });
        setMessages((prev) => [
          ...prev,
          { role: "user", content: question },
          { role: "assistant", content: response.data.answer }
        ]);
      } finally {
        setLoading(false);
      }
    },
    [api, ensureSession, videoId]
  );

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!input.trim()) {
      return;
    }
    const question = input.trim();
    setInput("");
    await sendQuestion(question);
  };

  const handleVoiceClick = async () => {
    // Placeholder for future Agora voice capture integration.
    alert("语音输入功能将在接入 Agora 后启用。");
  };

  return (
    <div className="flex h-full flex-col bg-slate-900/60">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-white">AI 培训助手</h3>
          <p className="text-xs text-slate-400">基于当前视频内容的智能问答</p>
        </div>
        <button
          onClick={handleVoiceClick}
          className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/20 text-primary transition hover:bg-primary/40"
          title="启动语音输入"
        >
          <MicrophoneIcon className="h-5 w-5" />
        </button>
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto px-4 py-3">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">
            向助手提问，例如：“这个视频里 TCP 三次握手的核心流程是什么？”
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={`rounded-lg px-3 py-2 text-sm ${
              message.role === "user"
                ? "bg-primary/30 text-white"
                : "bg-slate-800 text-slate-100"
            }`}
          >
            {message.content}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="border-t border-slate-800 px-4 py-3">
        <div className="flex items-center space-x-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="请输入问题..."
            className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-primary focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white transition hover:bg-primary-dark disabled:cursor-not-allowed disabled:bg-slate-700"
          >
            <PaperAirplaneIcon className="h-4 w-4" />
            发送
          </button>
        </div>
      </form>
    </div>
  );
};

export default AssistantPanel;
