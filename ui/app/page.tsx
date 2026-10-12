"use client";
import { useEffect, useMemo, useRef, useState } from "react";

type Task = {
  id: number;
  title: string;
  description: string;
  status: string;
  priority: string;
  due_date: string | null;
};

type ChatMessage = {
  role: "user" | "agent";
  content: string;
};

const BACKEND_HTTP = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";
const BACKEND_WS = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000/api/v1/chat";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [connected, setConnected] = useState(false);
  const [agentTyping, setAgentTyping] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Open WebSocket for chat
  useEffect(() => {
    const ws = new WebSocket(BACKEND_WS);
    wsRef.current = ws;
    ws.onopen = () => {
      setConnected(true);
      // Initial sync when socket connects
      void fetchTasks();
    };
    ws.onmessage = (event) => {
      const text = String(event.data);
      setMessages((prev) => [...prev, { role: "agent", content: text }]);
      setAgentTyping(false);
      // Trigger a refresh of tasks after agent replies (likely state changed)
      void fetchTasks();
    };
    ws.onerror = () => setConnected(false);
    ws.onclose = () => setConnected(false);
    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchTasks = useMemo(() => {
    return async () => {
      try {
        const res = await fetch(`${BACKEND_HTTP}/tasks/list`);
        const data = await res.json();
        setTasks(Array.isArray(data?.tasks) ? data.tasks : []);
      } catch (e) {
        // ignore for demo
      }
    };
  }, []);

  // Removed polling; task list updates only when agent responds or when toggles occur

  const sendMessage = () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setAgentTyping(true);
    wsRef.current?.send(input);
    setInput("");
  };

  const toggleStatus = async (task: Task) => {
    const nextStatus = task.status === "done" ? "pending" : "done";
    await fetch(`${BACKEND_HTTP}/tasks/update`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: task.id, status: nextStatus }),
    });
    await fetchTasks();
  };

  return (
    <div className="flex min-h-screen w-full bg-zinc-50 font-sans text-zinc-900 dark:bg-black dark:text-zinc-100">
      <main className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-6 p-6 md:grid-cols-2">
        {/* Chat Panel */}
        <section className="flex h-[94vh] flex-col rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <header className="flex items-center justify-between border-b border-zinc-200 p-4 text-sm dark:border-zinc-800">
            <div className="font-medium">Chat with Task Agent</div>
            <div className={`text-xs ${connected ? "text-emerald-600" : "text-zinc-500"}`}>
              {connected ? "Connected" : "Disconnected"}
            </div>
          </header>
          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.map((m, idx) => (
              <div key={idx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm leading-relaxed shadow-sm ${m.role === "user" ? "bg-blue-600 text-white" : "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"}`}>
                  {m.content}
                </div>
              </div>
            ))}
            {agentTyping && (
              <div className="flex justify-start">
                <div className="max-w-[70%] rounded-2xl bg-zinc-100 px-3 py-2 text-sm text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
                  <span className="inline-flex items-center gap-2">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 [animation-delay:-0.2s]"></span>
                    <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 [animation-delay:-0.1s]"></span>
                    <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400"></span>
                  </span>
                </div>
              </div>
            )}
          </div>
          <div className="flex gap-2 border-t border-zinc-200 p-3 dark:border-zinc-800">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") sendMessage();
              }}
              placeholder="e.g., Create a high priority task to buy milk tomorrow"
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500 dark:border-zinc-700 dark:bg-zinc-950"
            />
            <button
              onClick={sendMessage}
              className="rounded-md bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
              disabled={!connected}
            >
              Send
            </button>
          </div>
        </section>

        {/* Task List Panel */}
        <section className="h-[94vh] overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <header className="border-b border-zinc-200 p-4 text-sm font-medium dark:border-zinc-800">Tasks</header>
          <div className="h-full overflow-y-auto p-4">
            {tasks.length === 0 ? (
              <div className="text-sm text-zinc-500">No tasks yet. Ask the agent to create one.</div>
            ) : (
              <ul className="space-y-3">
                {tasks.map((t) => (
                  <li key={t.id} className="flex items-start justify-between gap-3 rounded-md border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                    <div className="flex flex-col">
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={t.status === "done"}
                          onChange={() => toggleStatus(t)}
                          className="h-4 w-4 accent-emerald-600"
                        />
                        <div className="font-medium">{t.title}</div>
                        <span className="rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                          {t.priority}
                        </span>
                      </div>
                      {t.description && (
                        <div className="mt-1 text-zinc-600 dark:text-zinc-400">{t.description}</div>
                      )}
                      {t.due_date && (
                        <div className="mt-1 text-xs text-zinc-500">Due: {new Date(t.due_date).toLocaleDateString()}</div>
                      )}
                    </div>
                    <div className="text-xs uppercase tracking-wide text-zinc-500">{t.status}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
