import axios from "axios";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === "register") {
        await axios.post("/api/v1/auth/register", { email, password });
      }
      await login(email, password);
      navigate("/library");
    } catch (err) {
      setError(mode === "login" ? "登录失败，请检查邮箱与密码" : "注册失败，请重试");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-6 rounded-xl border border-slate-800 bg-slate-900/70 p-8 shadow-xl"
      >
        <div>
          <h1 className="text-2xl font-semibold text-white">内部培训资料管理系统</h1>
          <p className="mt-2 text-sm text-slate-400">
            {mode === "login" ? "请输入邮箱与密码登录。" : "创建一个新账户以访问培训资料。"}
          </p>
        </div>
        {error && <div className="rounded-md bg-red-500/20 px-3 py-2 text-sm text-red-200">{error}</div>}
        <div className="space-y-2">
          <label className="block text-sm text-slate-300">邮箱</label>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 focus:border-primary focus:outline-none"
          />
        </div>
        <div className="space-y-2">
          <label className="block text-sm text-slate-300">密码</label>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 focus:border-primary focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-white transition hover:bg-primary-dark disabled:bg-slate-700"
        >
          {loading ? "处理中..." : mode === "login" ? "登录" : "注册并登录"}
        </button>
        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="w-full text-sm text-primary hover:text-primary-dark"
        >
          {mode === "login" ? "还没有账号？点击注册" : "已有账号？返回登录"}
        </button>
      </form>
    </div>
  );
};

export default LoginPage;
