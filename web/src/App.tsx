import { useEffect, useState, useRef } from 'react';
import { Terminal, Activity, Menu, Cpu } from 'lucide-react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

function App() {
  const [logs, setLogs] = useState<{ id: number, text: string, type: string }[]>([
    { id: 1, text: ">> 正在初始化终端引擎...", type: "sys" }
  ]);
  const [input, setInput] = useState('');
  const [sysStatus, setSysStatus] = useState({ state: 'connecting', sessionId: 'Waiting' });
  const terminalRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // 初始化 WebSocket
  useEffect(() => {
    // 处理开发环境 Vite proxy 和生产环境直连的不同
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.port === "5173" ? "127.0.0.1:8000" : window.location.host;
    const wsUrl = `${wsProtocol}//${host}/ws`;

    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onopen = () => {
      setLogs(prev => [...prev, { id: Date.now(), text: ">> 核心数据总线 WebSocket 连接成功", type: "success" }]);
      setSysStatus(s => ({ ...s, state: 'online' }));
    };

    socket.onmessage = (event) => {
      setLogs(prev => [...prev, { id: Date.now(), text: `[Daemon] ${event.data}`, type: "sys" }]);
    };

    socket.onclose = () => {
      setLogs(prev => [...prev, { id: Date.now(), text: ">> 核心数据总线中断", type: "error" }]);
      setSysStatus(s => ({ ...s, state: 'offline' }));
    };

    return () => socket.close();
  }, []);

  useEffect(() => {
    let active = true;
    const fetchHealth = async () => {
      if (!active) return;
      try {
        const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
        const res = await fetch(`${host}/health`);
        if (res.ok) {
          const data = await res.json();
          setSysStatus(s => ({ ...s, sessionId: data.session_id || 'Waiting' }));
        }
      } catch (err) {
        // failed
      } finally {
        if (active) {
          setTimeout(fetchHealth, 5000);
        }
      }
    };
    fetchHealth();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const handleSend = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && input.trim()) {
      const val = input.trim();
      setInput('');
      setLogs(prev => [...prev, { id: Date.now(), text: `[You] ${val}`, type: 'success' }]);

      if (val.startsWith('/')) {
        // WebSocket 指令下发
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(val);
        } else {
          setLogs(prev => [...prev, { id: Date.now(), text: ">> WebSocket 未连接无法发送实时指令", type: "error" }]);
        }
      } else {
        // REST API 普通对话
        try {
          const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
          const res = await fetch(`${host}/api/v1/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: val })
          });
          const data = await res.json();
          setLogs(prev => [...prev, {
            id: Date.now(),
            text: `[Agent] ${JSON.stringify(data.result?.response || data.result, null, 2)}`,
            type: 'sys'
          }]);
        } catch (e) {
          setLogs(prev => [...prev, { id: Date.now(), text: `>> API 请求失败`, type: "error" }]);
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-dark-900)] text-[#c9d1d9] flex flex-col p-4 md:p-8 font-mono">
      <header className="flex items-center justify-between border-b border-[var(--color-dark-border)] pb-4 mb-8">
        <div className="flex items-center gap-3 text-[var(--color-brand-500)]">
          <Terminal className="w-8 h-8" />
          <h1 className="text-2xl font-bold tracking-tight">Project Gemini-Claw</h1>
        </div>
        <div className="flex items-center gap-2">
          <Menu className="w-5 h-5 text-gray-400 cursor-pointer hover:text-white transition-colors" />
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
        <aside className="lg:col-span-1 space-y-6">
          <div className="bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl p-5 shadow-lg relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--color-brand-500)]/5 rounded-full blur-2xl -mr-10 -mt-10 transition-all group-hover:bg-[var(--color-brand-500)]/10" />
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-[var(--color-dark-900)] border border-[var(--color-dark-border)]">
                <Cpu className="w-5 h-5 text-[var(--color-brand-500)]" />
              </div>
              <h2 className="text-lg font-semibold text-white">生存状态卡片</h2>
            </div>

            <div className="space-y-4 relative z-10">
              <div className="flex justify-between items-center border-b border-[var(--color-dark-border)] pb-2">
                <span className="text-gray-400 text-sm">连接状态</span>
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className={cn("absolute inline-flex h-full w-full rounded-full opacity-75", sysStatus.state === 'online' ? "bg-green-400 animate-ping" : "bg-red-400")}></span>
                    <span className={cn("relative inline-flex rounded-full h-2 w-2", sysStatus.state === 'online' ? "bg-green-500" : "bg-red-500")}></span>
                  </span>
                  <span className={cn("text-sm font-medium", sysStatus.state === 'online' ? "text-[#3fb950]" : "text-red-500")}>
                    {sysStatus.state === 'online' ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center border-b border-[var(--color-dark-border)] pb-2">
                <span className="text-gray-400 text-sm">占用 Session ID</span>
                <span className="text-sm truncate w-40 text-right" title={sysStatus.sessionId}>{sysStatus.sessionId}</span>
              </div>
            </div>
          </div>

          <div className="bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl p-5 shadow-lg">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-[var(--color-dark-900)] border border-[var(--color-dark-border)]">
                <Activity className="w-5 h-5 text-purple-400" />
              </div>
              <h2 className="text-lg font-semibold text-white">活跃 Cron 队列</h2>
            </div>

            <ul className="space-y-3">
              <li className="text-sm flex justify-between px-3 py-2 bg-[var(--color-dark-900)] rounded-md border border-[var(--color-dark-border)]">
                <span className="text-gray-300">0 3 * * *</span>
                <span className="text-purple-300 truncate w-32 text-right">清理与记忆反思</span>
              </li>
              <li className="text-sm flex justify-between px-3 py-2 bg-[var(--color-dark-900)] rounded-md border border-[var(--color-dark-border)]">
                <span className="text-gray-300">*/30 * * * *</span>
                <span className="text-purple-300 truncate w-32 text-right">Heartbeat Pulse</span>
              </li>
            </ul>
          </div>
        </aside>

        <main className="lg:col-span-2 flex flex-col bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl overflow-hidden shadow-2xl relative max-h-[70vh]">

          <div className="bg-[#010409] px-4 py-3 border-b border-[var(--color-dark-border)] flex items-center justify-between">
            <span className="text-sm text-gray-400 font-semibold tracking-widest">&gt;&gt; TERMINAL OUTPOST</span>
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
            </div>
          </div>

          <div
            ref={terminalRef}
            className="flex-1 bg-[#010409] p-5 overflow-y-auto space-y-2"
          >
            {logs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  "text-[15px] leading-relaxed whitespace-pre-wrap",
                  log.type === "sys" ? "text-[#8b949e]" : "",
                  log.type === "success" ? "text-green-400" : "",
                  log.type === "error" ? "text-red-400 text-shadow-glow" : ""
                )}
              >
                {log.text}
              </div>
            ))}
          </div>

          <div className="p-4 bg-[var(--color-dark-700)] border-t border-[var(--color-dark-border)]">
            <div className="relative flex items-center">
              <span className="absolute left-4 text-[#58a6ff] font-bold">~ $</span>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleSend}
                placeholder="输入普通对话文字，或以 / 开头下发实时越权指令..."
                className="w-full bg-[#0d1117] text-[#c9d1d9] border border-[var(--color-dark-border)] rounded-lg py-3 pl-12 pr-4 focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff]/50 transition-all placeholder:text-gray-600"
                autoComplete="off"
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
