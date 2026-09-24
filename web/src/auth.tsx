import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { apiAdmin } from "./api";

// The admin token lives in sessionStorage only: it disappears when the tab closes
// and on logout. It is never put in a URL or in localStorage.
const KEY = "market-predict-admin-token";

const read = (): string | null => {
  try { return sessionStorage.getItem(KEY); } catch { return null; }
};

interface Auth {
  token: string | null;
  /** Verifies the token with the API first; throws ApiError if it is not accepted. */
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(read);

  const login = useCallback(async (t: string) => {
    await apiAdmin("GET", "/admin/check", t);
    try { sessionStorage.setItem(KEY, t); } catch { /* still logged in for this page view */ }
    setToken(t);
  }, []);

  const logout = useCallback(() => {
    try { sessionStorage.removeItem(KEY); } catch { /* ignore */ }
    setToken(null);
  }, []);

  const value = useMemo(() => ({ token, login, logout }), [token, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): Auth {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
