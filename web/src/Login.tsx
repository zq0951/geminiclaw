import React, { useState } from 'react';
import { Shield, Lock, ArrowRight, Loader2 } from 'lucide-react';
import CryptoJS from 'crypto-js';

interface LoginProps {
  onLoginSuccess: () => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const host = window.location.port === "5173" ? "http://127.0.0.1:8000" : "";
      const hashedPassword = CryptoJS.MD5(password).toString();
      const res = await fetch(`${host}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: hashedPassword })
      });
      const data = await res.json();

      if (res.ok && data.token) {
        localStorage.setItem('auth_token', data.token);
        onLoginSuccess();
      } else {
        setError(data.detail || '认证失败');
      }
    } catch (err: any) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-[#0d1117] flex items-center justify-center z-[100] p-6">
      <div className="w-full max-w-md relative animate-in fade-in zoom-in duration-500">
        <div className="bg-[#161b22] border border-[#30363d] rounded-[2rem] p-10 shadow-2xl relative overflow-hidden">
          {/* Header */}
          <div className="flex flex-col items-center mb-10 text-center relative z-10">
            <div className="h-16 w-16 bg-[#58a6ff] rounded-2xl flex items-center justify-center text-white mb-6 shadow-xl shadow-[#58a6ff]/20 transform rotate-3 scale-110">
              <Shield size={32} />
            </div>
            <h1 className="text-3xl font-black tracking-tighter text-[#c9d1d9] mb-2 uppercase">核心访问权限</h1>
            <p className="text-[#8b949e] text-sm font-medium tracking-wide uppercase">Gemini-Claw Protocol</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
            <div className="relative group">
              <div className="absolute inset-y-0 left-6 flex items-center text-[#8b949e] group-focus-within:text-[#58a6ff] transition-colors">
                <Lock size={20} />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入访问密钥(默认为claw)"
                className="w-full bg-[#0d1117] border border-[#30363d] focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] rounded-2xl py-4 pl-16 pr-6 text-[#c9d1d9] placeholder:text-[#8b949e] transition-all outline-none font-bold tracking-widest"
                autoFocus
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-[11px] font-black uppercase tracking-widest py-3 px-4 rounded-xl text-center">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#58a6ff] text-white hover:bg-[#3f83f8] disabled:bg-[#30363d] disabled:text-[#8b949e] font-black uppercase tracking-[0.2em] py-4 rounded-2xl transition-all flex items-center justify-center gap-3 relative overflow-hidden"
            >
              {loading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <>
                  <span>系统同步授权</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <div className="mt-10 pt-8 border-t border-[#30363d] flex flex-col items-center gap-2 relative z-10 text-center">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-[#1ca152] shadow-[0_0_8px_rgba(28,161,82,0.5)]" />
              <span className="text-[10px] font-black text-[#8b949e] uppercase tracking-[0.2em]">本地终端节点直连 - 密文传输</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
