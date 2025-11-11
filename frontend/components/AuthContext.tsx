import { createContext, useContext, useEffect, useState } from 'react';

interface AuthState {
  token: string | null;
  setToken: (token: string | null) => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem('sheetify-token');
    if (stored) {
      setTokenState(stored);
    }
  }, []);

  const setToken = (value: string | null) => {
    setTokenState(value);
    if (value) {
      window.localStorage.setItem('sheetify-token', value);
    } else {
      window.localStorage.removeItem('sheetify-token');
    }
  };

  return <AuthContext.Provider value={{ token, setToken }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
