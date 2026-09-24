import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";

export default function Login() {
  const { token, login } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? "/admin";
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (token) return <Navigate to="/admin" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(value.trim());
      navigate(from, { replace: true });
    } catch (err) {
      const e2 = err instanceof ApiError ? err : null;
      setError(
        e2?.status === 401 ? "That token wasn't accepted."
        : e2?.status === undefined ? `${e2?.message ?? "Something went wrong."} Is the API running?`
        : (e2 as ApiError).message,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-extrabold sm:text-3xl">Admin login</h1>
      <p className="mt-2 text-slate-600">
        For the person running this site. Everything else here is public and needs no login.
      </p>
      <form onSubmit={submit} className="mt-5 space-y-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-indigo-100 sm:p-6">
        <label className="block text-sm font-semibold text-slate-700" htmlFor="token">
          Admin token
        </label>
        <input
          id="token"
          type="password"
          autoComplete="off"
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
        />
        <p className="text-xs text-slate-500">
          The value of <code>ADMIN_TOKEN</code> in the server's <code>.env</code>. It is kept in this tab only and
          is cleared on logout or when the tab closes.
        </p>
        {error && (
          <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700 ring-1 ring-rose-200">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={busy || !value.trim()}
          className="w-full rounded-full bg-indigo-600 px-5 py-2 font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {busy ? "Checking…" : "Log in"}
        </button>
      </form>
    </div>
  );
}
