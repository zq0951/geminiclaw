import { useEffect, useState, useRef } from 'react';
import { Terminal, Cpu, FileText, LogOut, Plus, Trash2, ChevronDown, ChevronRight, X, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Login } from './Login';

export function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

function Dashboard({ onAuthFail }: { onAuthFail: () => void }) {
  const checkAuth = (res: Response) => {
    if (res.status === 401) {
      localStorage.removeItem('auth_token');
      onAuthFail();
      return false;
    }
    return true;
  };
  const [logs, setLogs] = useState<{ id: number, text: string, type: string, isMarkdown?: boolean }[]>([
    { id: 1, text: ">> 正在初始化终端引擎...", type: "sys" }
  ]);
  const [input, setInput] = useState('');
  const [model, setModel] = useState('auto');
  const [sysStatus, setSysStatus] = useState({ state: 'connecting', sessionId: 'Waiting' });
  const [skills, setSkills] = useState<string[]>([]);
  const [sessions, setSessions] = useState<{ id: string, desc: string }[]>([]);
  const [bounties, setBounties] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const terminalRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const isFetchingSessions = useRef(false);

  const [skillsCollapsed, setSkillsCollapsed] = useState(true);
  const [jobsCollapsed, setJobsCollapsed] = useState(true);
  const [selectedSkillDesc, setSelectedSkillDesc] = useState<{ name: string, content: string } | null>(null);
  const [isWaiting, setIsWaiting] = useState(false);

  // 初始化 WebSocket
  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connectWs = () => {
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.port === "5173" ? "127.0.0.1:8000" : window.location.host;
      const token = localStorage.getItem('auth_token') || '';
      const wsUrl = `${wsProtocol}//${host}/ws?token=${token}`;

      socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setLogs(prev => [...prev, { id: Date.now(), text: ">> 核心数据总线 WebSocket 连接成功", type: "success" }]);
        setSysStatus(s => ({ ...s, state: 'online' }));
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'message' && data.role === 'assistant' && data.content) {
            setIsWaiting(false);
            setLogs(prev => {
              const lastLog = prev[prev.length - 1];
              if (lastLog && (lastLog.type === 'agent-stream' || lastLog.type === 'agent-stream-rest')) {
                return [...prev.slice(0, -1), { ...lastLog, text: lastLog.text + data.content }];
              } else {
                return [...prev, { id: Date.now(), text: data.content, type: "agent-stream", isMarkdown: true }];
              }
            });
          }
        } catch (e) {
          setLogs(prev => [...prev, { id: Date.now(), text: `[Daemon] ${event.data}`, type: "sys" }]);
        }
      };

      socket.onclose = () => {
        setLogs(prev => {
          if (prev.length > 0 && prev[prev.length - 1].text.includes("尝试重连")) return prev;
          return [...prev, { id: Date.now(), text: ">> 核心数据总线中断，尝试重连中...", type: "error" }];
        });
        setSysStatus(s => ({ ...s, state: 'offline' }));
        reconnectTimer = setTimeout(connectWs, 3000);
      };
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimer);
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
    };
  }, []);

  const fetchData = () => {
    try {
      const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
      const headers = { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` };

      fetch(`${host}/api/v1/skills`, { headers })
        .then(res => { if (checkAuth(res) && res.ok) return res.json(); })
        .then(data => { if (data) setSkills(data.skills || []); })
        .catch(() => { });

      fetch(`${host}/api/v1/bounties`, { headers })
        .then(res => { if (checkAuth(res) && res.ok) return res.json(); })
        .then(data => { if (data) setBounties(data); })
        .catch(() => { });

      fetch(`${host}/api/v1/jobs`, { headers })
        .then(res => { if (checkAuth(res) && res.ok) return res.json(); })
        .then(data => { if (data) setJobs(data); })
        .catch(() => { });

      if (!isFetchingSessions.current) {
        isFetchingSessions.current = true;
        fetch(`${host}/api/v1/sessions`, { headers })
          .then(res => { if (checkAuth(res) && res.ok) return res.json(); })
          .then(data => {
            if (data) {
              setSessions(data.sessions || []);
              if (data.current_session_id) setSysStatus(s => ({ ...s, sessionId: data.current_session_id }));
            }
          })
          .catch(() => { })
          .finally(() => { isFetchingSessions.current = false; });
      }
    } catch (err) { }
  };

  useEffect(() => {
    fetchData(); // 初始加载其他轻量状态，如果需要初始会话可以通过专门的方法

    // We only poll light-weight stats every 10s: skills, bounties, jobs.
    // The session listing (which spawns a heavyweight node process) shouldn't be polled blindly.
    const interval = setInterval(() => {
        try {
            const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
            const headers = { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` };
            
            fetch(`${host}/api/v1/skills`, { headers })
              .then(res => { if (checkAuth(res) && res.ok) return res.json(); })
              .then(data => { if (data) setSkills(data.skills || []); })
              .catch(() => { });

            fetch(`${host}/api/v1/bounties`, { headers })
              .then(res => { if (checkAuth(res) && res.ok) return res.json(); })
              .then(data => { if (data) setBounties(data); })
              .catch(() => { });

            fetch(`${host}/api/v1/jobs`, { headers })
              .then(res => { if (checkAuth(res) && res.ok) return res.json(); })
              .then(data => { if (data) setJobs(data); })
              .catch(() => { });
        } catch(e) {}
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchSessionsList = () => {
    if (isFetchingSessions.current) return;
    try {
        const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
        const headers = { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` };
        isFetchingSessions.current = true;
        fetch(`${host}/api/v1/sessions`, { headers })
          .then(res => { if (checkAuth(res) && res.ok) return res.json(); })
          .then(data => {
            if (data) {
              setSessions(data.sessions || []);
              if (data.current_session_id && !sysStatus.sessionId) {
                  setSysStatus(s => ({ ...s, sessionId: data.current_session_id }));
              }
            }
          })
          .catch(() => { })
          .finally(() => { isFetchingSessions.current = false; });
    } catch(err) {
        isFetchingSessions.current = false;
    }
  };

  useEffect(() => {
    fetchSessionsList(); // Start by fetching the list exactly once when opening
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
  }, [logs, isWaiting]);

  const loadHistoryStable = async (sessionId: string, init = false) => {
    try {
      const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
      const res = await fetch(`${host}/api/v1/sessions/history?session_id=${sessionId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      });
      if (!checkAuth(res)) return;
      if (res.ok) {
        const data = await res.json();
        setLogs(prevLogs => {
          if (!data.history || data.history.length === 0) {
            if (init) return [{ id: Date.now(), text: `>> 建立全新交互通道: ${sessionId}`, type: "sys" }];
            return prevLogs;
          }

          const existingHistoryLogs = prevLogs.filter(l => l.type === 'agent-stream-rest' || l.type === 'success');
          let lastExistingText = existingHistoryLogs.length > 0 ? existingHistoryLogs[existingHistoryLogs.length - 1].text : '';
          let lastFetchedMsg = data.history[data.history.length - 1];
          let lastFetchedText = lastFetchedMsg.role === 'user' ? `[You] ${lastFetchedMsg.content}` : lastFetchedMsg.content;

          if (existingHistoryLogs.length === data.history.length && lastExistingText === lastFetchedText && !init) {
            return prevLogs;
          }

          const newLogs = data.history.map((msg: any, i: number) => ({
            id: 10000 + i,
            text: msg.role === 'user' ? `[You] ${msg.content}` : msg.content,
            type: msg.role === 'user' ? 'success' : 'agent-stream-rest',
            isMarkdown: msg.role !== 'user'
          }));

          return [
            { id: 1, text: `>> 加载会话历史: ${sessionId}`, type: "sys" },
            ...newLogs
          ];
        });
      }
    } catch (e) { }
  };

  useEffect(() => {
    if (!sysStatus.sessionId || sysStatus.sessionId === 'Waiting') return;
    loadHistoryStable(sysStatus.sessionId, true);
  }, [sysStatus.sessionId]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (sysStatus.sessionId && sysStatus.sessionId !== 'Waiting' && !isWaiting) {
      interval = setInterval(() => {
        loadHistoryStable(sysStatus.sessionId, false);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [sysStatus.sessionId, isWaiting]);

  const switchSession = async (sessionId: string) => {
    try {
      const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
      const res = await fetch(`${host}/api/v1/sessions/switch`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({ session_id: sessionId })
      });
      if (!checkAuth(res)) return;
      if (res.ok) {
        const data = await res.json();
        setSysStatus(s => ({ ...s, sessionId: data.session_id }));
        setLogs(prev => [...prev, { id: Date.now(), text: `>> 切换到会话: ${sessionId}`, type: "success" }]);
      }
    } catch (e) {
      // ignore
    }
  }

  const deleteSession = async (sessionId: string) => {
    if (!confirm('确定删除此会话吗？')) return;
    try {
      const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
      const res = await fetch(`${host}/api/v1/sessions/${sessionId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      if (checkAuth(res) && res.ok) {
        setLogs(prev => [...prev, { id: Date.now(), text: `>> 已删除会话: ${sessionId}`, type: "sys" }]);
        fetchSessionsList(); // 重新加载列表
      }
    } catch (e) {
      // ignore
    }
  }

  const fetchSkillDesc = async (skill: string) => {
    try {
      const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
      const res = await fetch(`${host}/api/v1/skills/${skill}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      });
      if (checkAuth(res) && res.ok) {
        const data = await res.json();
        setSelectedSkillDesc(data);
      }
    } catch (err) { }
  };

  const handleNewSession = async () => {
    try {
      const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
      const res = await fetch(`${host}/api/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({ prompt: "/new" })
      });
      if (!checkAuth(res)) return;
      if (res.ok) {
        setLogs([{ id: Date.now(), text: ">> 开启了全新的会话！", type: "success" }]);
        setSysStatus(s => ({ ...s, sessionId: '' }));
      }
    } catch (e) {
      setLogs(prev => [...prev, { id: Date.now(), text: `>> 新对话请求失败`, type: "error" }]);
    }
  };

  const handleSend = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && input.trim() && !isWaiting) {
      const val = input.trim();
      setInput('');
      setLogs(prev => [...prev, { id: Date.now(), text: `[You] ${val}`, type: 'success' }]);
      setIsWaiting(true);

      // REST API 采用流式读取 SSE (Server-Sent Events 格式)
      try {
        const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
        const res = await fetch(`${host}/api/v1/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem('auth_token')}`
          },
          body: JSON.stringify({ prompt: val, model: model }),
          keepalive: true // 告诉浏览器尽量保持这个长连接，防意外销毁
        });

        if (!checkAuth(res)) {
          setIsWaiting(false);
          return;
        }

        if (!res.body) {
          setIsWaiting(false);
          throw new Error("No response body");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              try {
                const event = JSON.parse(dataStr);
                if (event.type === 'init' && event.session_id) {
                  setSysStatus(s => ({ ...s, sessionId: event.session_id }));
                } else if (event.type === 'message' && event.role === 'assistant' && event.content) {
                  setIsWaiting(false);
                  setLogs(prev => {
                    const lastLog = prev[prev.length - 1];
                    if (lastLog && lastLog.type === 'agent-stream-rest') {
                      return [...prev.slice(0, -1), { ...lastLog, text: lastLog.text + event.content }];
                    } else {
                      return [...prev, { id: Date.now(), text: event.content, type: "agent-stream-rest", isMarkdown: true }];
                    }
                  });
                } else if (event.type === 'error') {
                  setIsWaiting(false);
                  setLogs((prev) => [
                    ...prev,
                    {
                      id: Date.now(),
                      text: `>> [Core Error] ${event.message}\n${event.details || ''}`,
                      type: 'error'
                    }
                  ]);
                }
              } catch (e) {
                // unparsable line
              }
            }
          }
        }
        setIsWaiting(false);
      } catch (e) {
        setIsWaiting(false);
        setLogs(prev => [...prev, { id: Date.now(), text: `>> API 请求失败`, type: "error" }]);
      }
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-dark-900)] text-[#c9d1d9] flex flex-col p-4 md:p-8 font-mono relative">
      <header className="flex items-center justify-between border-b border-[var(--color-dark-border)] pb-4 mb-8">
        <div className="flex items-center gap-3 text-[var(--color-brand-500)]">
          <Terminal className="w-8 h-8" />
          <h1 className="text-2xl font-bold tracking-tight">Project Gemini-Claw</h1>
        </div>
        <div className="flex items-center gap-2 relative">
          <button
            onClick={() => { localStorage.removeItem('auth_token'); onAuthFail(); }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors text-sm font-medium border border-red-500/20"
            title="退出/清除访问密钥"
          >
            <LogOut className="w-4 h-4" />
            <span>退出终端</span>
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 relative">
        <aside className="lg:col-span-1 space-y-6 max-h-[80vh] overflow-y-auto pr-2 pb-2">
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
                <span className="text-sm truncate w-40 text-right" title={sysStatus.sessionId}>{sysStatus.sessionId || 'None'}</span>
              </div>
            </div>
          </div>

          <div className="bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl p-5 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-[var(--color-dark-900)] border border-[var(--color-dark-border)]">
                  <FileText className="w-5 h-5 text-blue-400" />
                </div>
                <h2 className="text-lg font-semibold text-white">关联的会话</h2>
                <button onClick={(e) => { e.stopPropagation(); fetchSessionsList(); }} title="刷新" className="p-1 hover:bg-[var(--color-dark-900)] rounded text-gray-400 hover:text-white transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                </button>
              </div>
            </div>

            <ul className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {sessions.map(s => (
                <li key={s.id} className={cn("flex flex-col text-sm px-3 py-2 bg-[var(--color-dark-900)] rounded-md border border-[var(--color-dark-border)] hover:border-[#58a6ff] transition-colors group", sysStatus.sessionId === s.id ? 'border-[#58a6ff]' : '')}>
                  <div className="flex justify-between items-start cursor-pointer" onClick={() => switchSession(s.id)}>
                    <div className="truncate font-semibold text-gray-300 w-full pr-2">{s.desc}</div>
                  </div>
                  <div className="flex justify-between items-center mt-1">
                    <div className="text-xs text-gray-500 truncate cursor-pointer" onClick={() => switchSession(s.id)}>{s.id}</div>
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                      className="text-red-400 opacity-0 group-hover:opacity-100 hover:text-red-300 transition-opacity p-1"
                      title="删除会话"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </li>
              ))}
              {sessions.length === 0 && <span className="text-sm text-gray-500">暂无会话记录</span>}
            </ul>
          </div>

          <div className="bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl p-5 shadow-lg">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-[var(--color-dark-900)] border border-[var(--color-dark-border)]">
                <Plus className="w-5 h-5 text-yellow-400" />
              </div>
              <h2 className="text-lg font-semibold text-white">全自动打工看板</h2>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {bounties.map(b => (
                <div key={b.id} className="text-xs p-2 bg-[var(--color-dark-900)] rounded border border-[var(--color-dark-border)]">
                  <div className="flex justify-between font-bold text-gray-300">
                    <span>{b.platform}</span>
                    <span className={cn(b.status === 'SUCCESS' ? 'text-green-400' : 'text-yellow-400')}>{b.status}</span>
                  </div>
                  <div className="truncate my-1">{b.title}</div>
                  <div className="text-[10px] text-blue-400">{b.reward_amount} {b.reward_currency}</div>
                </div>
              ))}
              {bounties.length === 0 && <span className="text-sm text-gray-500">寻找猎物中...</span>}
            </div>
          </div>

          <div className="bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl p-5 shadow-lg">
            <div
              className="flex items-center justify-between mb-2 cursor-pointer select-none group"
              onClick={() => setJobsCollapsed(!jobsCollapsed)}
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-[var(--color-dark-900)] border border-[var(--color-dark-border)] group-hover:border-purple-400 transition-colors">
                  <Plus className="w-5 h-5 text-purple-400" />
                </div>
                <h2 className="text-lg font-semibold text-white">Cron 调度中心</h2>
              </div>
              <div className="text-gray-400">
                {jobsCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </div>
            </div>
            {!jobsCollapsed && (
              <div className="space-y-2 text-[10px] text-gray-400 mt-4">
                {jobs.map((j, i) => (
                  <div key={i} className="p-1 border-b border-[var(--color-dark-border)] last:border-0 truncate">
                    {j.info}
                  </div>
                ))}
                {jobs.length === 0 && <span>暂无活跃任务</span>}
              </div>
            )}
          </div>

          <div className="bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl p-5 shadow-lg">
            <div
              className="flex items-center justify-between mb-2 cursor-pointer select-none group"
              onClick={() => setSkillsCollapsed(!skillsCollapsed)}
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-[var(--color-dark-900)] border border-[var(--color-dark-border)] group-hover:border-green-400 transition-colors">
                  <Cpu className="w-5 h-5 text-green-400" />
                </div>
                <h2 className="text-lg font-semibold text-white">可用技能库</h2>
              </div>
              <div className="text-gray-400">
                {skillsCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </div>
            </div>

            {!skillsCollapsed && (
              <div className="flex flex-wrap gap-2 mt-4">
                {skills.map(skill => (
                  <div
                    key={skill}
                    onClick={() => fetchSkillDesc(skill)}
                    className="px-3 py-1.5 bg-[var(--color-dark-900)] border border-[var(--color-dark-border)] rounded-full text-xs text-gray-300 hover:border-green-400 hover:text-white transition-colors cursor-pointer"
                  >
                    {skill}
                  </div>
                ))}
                {skills.length === 0 && <span className="text-sm text-gray-500">暂无可用技能</span>}
              </div>
            )}
          </div>
        </aside>

        <main className="lg:col-span-3 flex flex-col bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl overflow-hidden shadow-2xl relative max-h-[80vh]">
          <div className="bg-[#010409] px-4 py-3 border-b border-[var(--color-dark-border)] flex items-center justify-between">
            <span className="text-sm text-gray-400 font-semibold tracking-widest">&gt;&gt; TERMINAL OUTPOST</span>

            <div className="flex items-center gap-3">
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="bg-[var(--color-dark-700)] text-xs text-gray-300 border border-[var(--color-dark-border)] rounded-md px-2 py-1 outline-none focus:border-[#58a6ff]"
              >
                <option value="auto">auto (CLI 默认)</option>
                <option value="gemini-3.1-pro-preview">gemini-3.1-pro-preview</option>
                <option value="gemini-3-flash-preview">gemini-3-flash-preview</option>
                <option value="gemini-2.5-pro">gemini-2.5-pro</option>
                <option value="gemini-2.5-flash">gemini-2.5-flash</option>
                <option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite</option>
              </select>

              <button
                onClick={handleNewSession}
                className="flex items-center gap-1 bg-[#1f6feb] hover:bg-[#388bfd] text-white px-3 py-1 rounded-md text-xs font-medium transition-colors border border-[rgba(240,246,252,0.1)] shadow-sm"
                title="开启新会话 (重置当前对话状态)"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>新对话</span>
              </button>

              <div className="flex gap-1.5 ml-2">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
            </div>
          </div>

          <div
            ref={terminalRef}
            className="flex-1 bg-[#010409] p-5 overflow-y-auto space-y-4"
          >
            {logs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  "text-[15px] leading-relaxed",
                  log.type === "sys" ? "text-[#8b949e]" : "",
                  log.type === "success" ? "text-green-400" : "",
                  log.type === "error" ? "text-red-400 text-shadow-glow" : "",
                  (log.type === "agent-stream" || log.type === "agent-stream-rest") ? "text-[#e6edf3] p-3 border border-[#30363d] bg-[#0d1117] rounded-lg shadow-sm" : ""
                )}
              >
                {log.isMarkdown ? (
                  <div className="prose prose-invert prose-p:my-1 prose-pre:bg-[#161b22] prose-pre:border prose-pre:border-[#30363d] prose-h1:text-xl max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        img: ({ node, ...props }) => (
                          <div className="my-4 relative group">
                            <img
                              {...props}
                              className="rounded-lg border border-[#30363d] max-w-full h-auto shadow-2xl transition-transform hover:scale-[1.02] cursor-zoom-in"
                              loading="lazy"
                            />
                            <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur-sm px-2 py-1 rounded text-[10px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                              4K Ultra HD
                            </div>
                          </div>
                        )
                      }}
                    >
                      {log.text}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="whitespace-pre-wrap">{log.text}</div>
                )}
              </div>
            ))}
            {isWaiting && (
              <div className="flex items-center gap-2 text-[#8b949e] text-sm animate-pulse p-2">
                <Loader2 className="w-4 h-4 animate-spin text-[#58a6ff]" />
                <span>等待核心大脑响应中...</span>
              </div>
            )}
          </div>

          <div className="p-4 bg-[var(--color-dark-700)] border-t border-[var(--color-dark-border)]">
            <div className="relative flex items-center">
              <span className="absolute left-4 text-[#58a6ff] font-bold">~ $</span>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleSend}
                disabled={isWaiting}
                placeholder="输入普通对话文字，或以 / 开头下发系统级指令 (如 /new 开启新对话)..."
                className="w-full bg-[#0d1117] text-[#c9d1d9] border border-[var(--color-dark-border)] rounded-lg py-3 pl-12 pr-4 focus:outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff]/50 transition-all placeholder:text-gray-600 disabled:opacity-50"
                autoComplete="off"
              />
            </div>
          </div>
        </main>
      </div>

      {/* Skill Config Modal */}
      {selectedSkillDesc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-[var(--color-dark-700)] border border-[var(--color-dark-border)] rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="bg-[var(--color-dark-900)] px-4 py-3 border-b border-[var(--color-dark-border)] flex items-center justify-between">
              <h3 className="text-white font-bold flex items-center gap-2">
                <Cpu className="w-4 h-4 text-green-400" />
                技能说明: {selectedSkillDesc.name}
              </h3>
              <button onClick={() => setSelectedSkillDesc(null)} className="text-gray-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto bg-[#0d1117] flex-1">
              <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap leading-relaxed">
                {selectedSkillDesc.content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  const [authenticated, setAuthenticated] = useState<boolean>(() => !!localStorage.getItem('auth_token'));

  if (!authenticated) {
    return <Login onLoginSuccess={() => setAuthenticated(true)} />;
  }

  return <Dashboard onAuthFail={() => setAuthenticated(false)} />;
}

export default App;
