import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

export const Login: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        // Register flow
        await api.post("/auth/register", {
          email,
          password,
          full_name: fullName,
          role: "admin", // register first user as admin for simplicity
        });
        
        // Auto login
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        const loginRes = await api.post("/auth/login", formData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });
        await login(loginRes.data.access_token);
        navigate("/");
      } else {
        // Login flow
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        const loginRes = await api.post("/auth/login", formData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });
        await login(loginRes.data.access_token);
        navigate("/");
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Authentication failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen flex items-center justify-center bg-slate-950 text-slate-100 relative overflow-hidden">
      {/* Visual background grids */}
      <div className="absolute w-96 h-96 bg-brand-500/10 rounded-full blur-3xl -top-12 -left-12"></div>
      <div className="absolute w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -bottom-12 -right-12"></div>

      <div className="w-full max-w-md p-8 rounded-2xl glass shadow-2xl relative z-10 flex flex-col gap-6">
        <div className="flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-xl bg-brand-500 flex items-center justify-center font-bold text-white shadow-xl shadow-brand-500/30 text-xl">
            Ω
          </div>
          <h2 className="text-xl font-bold text-white mt-3">
            {isRegister ? "Create Admin Account" : "Access Console"}
          </h2>
          <p className="text-slate-400 text-xs font-semibold">
            {isRegister ? "Register system administrator session" : "Sign in to manage scheduling runs"}
          </p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg p-3 text-xs font-semibold">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {isRegister && (
            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Full Name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Admin user"
                className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3.5 py-2.5 text-xs text-slate-200 transition"
              />
            </div>
          )}

          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@scheduler.io"
              className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3.5 py-2.5 text-xs text-slate-200 transition"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3.5 py-2.5 text-xs text-slate-200 transition"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 text-white rounded-lg py-2.5 text-xs font-bold transition mt-2 shadow-lg shadow-brand-500/20"
          >
            {loading ? "AUTHENTICATING..." : isRegister ? "REGISTER SESSION" : "SIGN IN"}
          </button>
        </form>

        <div className="text-center">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-xs font-semibold text-brand-400 hover:underline transition"
          >
            {isRegister ? "Already registered? Sign in" : "Register a new administrator"}
          </button>
        </div>
      </div>
    </div>
  );
};
