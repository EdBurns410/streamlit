import { FormEvent, useState } from 'react';
import api from '../lib/api';
import { useAuth } from './AuthContext';

interface AuthFormsProps {
  onAuthenticated?: () => void;
}

export function AuthForms({ onAuthenticated }: AuthFormsProps) {
  const { token, setToken } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === 'register') {
        await api.post('/v1/auth/register', { email, password });
      }
      const form = new FormData();
      form.append('username', email);
      form.append('password', password);
      const { data } = await api.post('/v1/auth/token', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      setToken(data.access_token);
      onAuthenticated?.();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to authenticate');
    } finally {
      setLoading(false);
    }
  };

  if (token) {
    return null;
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl w-full max-w-md">
      <h2 className="text-xl font-semibold text-white mb-2">Welcome to Sheetify Studio</h2>
      <p className="text-sm text-slate-400 mb-4">Sign in or create an account to deploy Streamlit tools.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300">Email</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300">Password</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            required
          />
        </div>
        {error && <div className="rounded-md bg-red-900/40 border border-red-500 px-3 py-2 text-sm text-red-200">{error}</div>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-indigo-500 py-2 font-semibold text-white hover:bg-indigo-400 disabled:opacity-50"
        >
          {loading ? 'Processing…' : mode === 'login' ? 'Sign In' : 'Create Account'}
        </button>
      </form>
      <button
        onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
        className="mt-4 text-sm text-indigo-300 hover:text-indigo-200"
      >
        {mode === 'login' ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
      </button>
    </div>
  );
}
