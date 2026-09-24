import { API_URL, type ApiError } from "../api";

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div role="status" className="animate-pulse rounded-2xl bg-white/70 p-6 text-sm text-slate-400 ring-1 ring-indigo-100">
      {label}
    </div>
  );
}

/** Never shows a number: only what went wrong and how to fix it. */
export function ErrorBox({ error, retry }: { error: ApiError; retry: () => void }) {
  const down = error.status === undefined;
  const notStored = error.status === 404;
  return (
    <div
      role="alert"
      className={`rounded-2xl p-5 ring-1 ${
        notStored ? "bg-slate-50 ring-slate-200" : "bg-rose-50 ring-rose-200"
      }`}
    >
      <p className={`font-bold ${notStored ? "text-slate-700" : "text-rose-700"}`}>
        {down ? "The forecast API is not reachable" : notStored ? "Nothing to show yet" : "Something went wrong"}
      </p>
      <p className="mt-1 text-sm text-slate-600">{error.message}</p>
      {down && (
        <p className="mt-2 text-sm text-slate-600">
          Start it from the project folder with{" "}
          <code className="rounded bg-white px-1.5 py-0.5 text-xs ring-1 ring-rose-200">uvicorn api.main:app --reload</code>{" "}
          (expected at {API_URL}).
        </p>
      )}
      <button
        onClick={retry}
        className="mt-3 rounded-full bg-indigo-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-indigo-700"
      >
        Try again
      </button>
    </div>
  );
}
