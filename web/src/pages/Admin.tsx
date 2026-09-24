import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, apiAdmin, apiGet, type StatusResponse } from "../api";
import { useAuth } from "../auth";

type Run =
  | { phase: "idle" }
  | { phase: "working"; text: string }
  | { phase: "done"; ok: boolean; text: string }
  | { phase: "error"; text: string };

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function JobPanel(props: { title: string; blurb: string; button: string; job: string; path: string }) {
  const { token, logout } = useAuth();
  const [run, setRun] = useState<Run>({ phase: "idle" });

  const lastRun = async (job: string) =>
    (await apiGet<StatusResponse>("/status")).jobs.find((j) => j.job_name === job);

  async function start() {
    if (!token) return;
    setRun({ phase: "working", text: "Starting…" });
    try {
      const before = await lastRun(props.job);
      await apiAdmin("POST", props.path, token);
      setRun({ phase: "working", text: "Started. Waiting for the job to finish…" });
      // The API starts the job in its own process; poll /status until a NEW run has finished.
      for (let i = 0; i < 30; i++) {
        await sleep(1000);
        const now = await lastRun(props.job);
        if (now && now.started_at !== before?.started_at && now.finished_at) {
          setRun({ phase: "done", ok: now.status === "ok", text: `${now.status}: ${now.message ?? ""}` });
          return;
        }
      }
      setRun({ phase: "done", ok: true, text: "Started, but it is taking a while. Check the Status page." });
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) logout(); // token no longer valid
      setRun({ phase: "error", text: e instanceof ApiError ? e.message : String(e) });
    }
  }

  const working = run.phase === "working";
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-indigo-100 sm:p-6">
      <h2 className="font-bold">{props.title}</h2>
      <p className="mt-1 text-sm text-slate-600">{props.blurb}</p>
      <button
        onClick={start}
        disabled={working}
        className="mt-4 rounded-full bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-wait disabled:bg-slate-300"
      >
        {working ? "Running…" : props.button}
      </button>
      {run.phase === "working" && <p role="status" className="mt-3 text-sm text-slate-500">{run.text}</p>}
      {run.phase === "done" && (
        <p role="status" className={`mt-3 rounded-lg px-3 py-2 text-sm ${run.ok ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-700"}`}>
          {run.text}
        </p>
      )}
      {run.phase === "error" && (
        <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{run.text}</p>
      )}
    </section>
  );
}

export default function Admin() {
  const { token, logout } = useAuth();
  const [checked, setChecked] = useState(false);

  // A stored token can go stale (server restarted with a new ADMIN_TOKEN): re-verify on open.
  useEffect(() => {
    if (!token) return;
    apiAdmin("GET", "/admin/check", token)
      .then(() => setChecked(true))
      .catch((e) => { if (e instanceof ApiError && e.status === 401) logout(); else setChecked(true); });
  }, [token, logout]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold sm:text-3xl">Admin</h1>
          <p className="text-sm text-slate-500">Logged in. These buttons start the existing jobs; nothing here trains a model.</p>
        </div>
        <button onClick={logout} className="rounded-full bg-slate-100 px-4 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-200">
          Log out
        </button>
      </div>

      {!checked ? (
        <p className="text-sm text-slate-400">Checking your login…</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <JobPanel
            title="Refresh prices"
            blurb="Re-reads the cached daily price files and upserts them into the database. Safe to repeat; it never creates duplicate rows."
            button="Refresh prices"
            job="refresh_prices"
            path="/admin/refresh"
          />
          <JobPanel
            title="Write forecasts"
            blurb="Runs the saved models on the latest prices and upserts one forecast per market. Safe to repeat; a same-day run overwrites, it does not add rows."
            button="Write forecasts"
            job="write_forecasts"
            path="/admin/write-forecasts"
          />
          <section className="rounded-2xl bg-slate-50 p-5 ring-1 ring-slate-200 sm:p-6 md:col-span-2">
            <h2 className="font-bold text-slate-500">Retrain models</h2>
            <p className="mt-1 text-sm text-slate-500">
              Not in this phase. Retraining is not available over HTTP; it runs offline with scripts/run_pipeline.py and scripts/select_models.py.
            </p>
            <button disabled className="mt-4 cursor-not-allowed rounded-full bg-slate-200 px-5 py-2 text-sm font-semibold text-slate-400">
              Retrain (not in this phase)
            </button>
          </section>
        </div>
      )}
      <p className="text-sm text-slate-500">
        See the result on the <Link to="/status" className="font-semibold text-indigo-600 underline">Status page</Link>.
      </p>
    </div>
  );
}
