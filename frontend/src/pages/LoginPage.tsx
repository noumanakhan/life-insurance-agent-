import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock, Loader2, AlertCircle } from 'lucide-react';
import api from '../lib/api';
import { useAuthStore } from '../store';
import type { TokenResponse } from '../types';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<TokenResponse>('/auth/login', { email, password });
      return res.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('token', data.access_token);
      setAuth(data.access_token, data.user_id, data.email);
      navigate('/chat');
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Login failed. Please check your credentials.');
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError('');
    mutation.mutate();
  };

  return (
    <div className="animated-bg min-h-screen flex items-center justify-center p-4">
      <div className="glass w-full max-w-md p-8 fade-in">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-4 shadow-lg shadow-blue-500/30">
            <Shield size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold gradient-text">Life Insurance AI</h1>
          <p style={{ color: 'var(--c-text-muted)' }} className="text-sm mt-1">Sign in to your advisor</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--c-text-muted)' }}>
              Email address
            </label>
            <div className="relative">
              <Mail size={16} className="absolute left-3 top-3.5" style={{ color: 'var(--c-text-muted)' }} />
              <input
                id="login-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="chat-input w-full pl-10 pr-4 py-3 text-sm"
                placeholder="you@example.com"
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--c-text-muted)' }}>
              Password
            </label>
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-3.5" style={{ color: 'var(--c-text-muted)' }} />
              <input
                id="login-password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="chat-input w-full pl-10 pr-4 py-3 text-sm"
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          <button
            id="login-submit"
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary w-full py-3 flex items-center justify-center gap-2"
          >
            {mutation.isPending ? <Loader2 size={18} className="animate-spin" /> : null}
            {mutation.isPending ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-sm mt-6" style={{ color: 'var(--c-text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/register" className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
