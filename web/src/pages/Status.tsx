import { useApi, type StatusResponse } from "../api";
import { ErrorBox, Loading } from "../components/ApiState";
import { dateTime, shortDate } from "../format";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-indigo-100">
      <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-indigo-600">{title}</h2>
      <div className="overflow-x-auto">{children}</div>
    </section>
  );
}

const th = "px-2 py-2 text-left text-xs font-semibold text-slate-400";
const td = "px-2 py-2 align-top";

export default function Status() {
  const { data, error, loading, retry } = useApi<StatusResponse>("/status");
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold sm:text-3xl">Status</h1>
        <p className="mt-1 text-slate-600">When the data and forecast jobs last ran, and how fresh each market is.</p>
      </div>
      {loading && <Loading />}
      {error && <ErrorBox error={error} retry={retry} />}
      {data && (
        <>
          <Section title="Last job runs">
            {data.jobs.length === 0 ? (
              <p className="text-sm text-slate-500">No jobs have run yet.</p>
            ) : (
              <table className="w-full min-w-[560px] text-sm">
                <thead><tr><th className={th}>Job</th><th className={th}>Status</th><th className={th}>Started</th><th className={th}>Finished</th><th className={th}>Message</th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {data.jobs.map((j) => (
                    <tr key={j.job_name}>
                      <td className={`${td} font-semibold`}>{j.job_name}</td>
                      <td className={td}>
                        <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${
                          j.status === "ok" ? "bg-emerald-100 text-emerald-700"
                          : j.status === "error" ? "bg-rose-100 text-rose-700" : "bg-amber-100 text-amber-700"
                        }`}>{j.status}</span>
                      </td>
                      <td className={td}>{dateTime(j.started_at)}</td>
                      <td className={td}>{dateTime(j.finished_at)}</td>
                      <td className={`${td} max-w-xs text-xs text-slate-500`}>{j.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Section>
          <div className="grid gap-5 md:grid-cols-2">
            <Section title="Forecast dates (as of)">
              <table className="w-full text-sm">
                <thead><tr><th className={th}>Market</th><th className={th}>Latest as of</th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {data.forecasts.map((f) => (
                    <tr key={f.ticker}><td className={`${td} font-semibold`}>{f.ticker}</td><td className={td}>{shortDate(f.latest_as_of)}</td></tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Price data">
              <table className="w-full text-sm">
                <thead><tr><th className={th}>Market</th><th className={th}>Latest date</th><th className={th}>Rows</th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {data.prices.map((p) => (
                    <tr key={p.ticker}><td className={`${td} font-semibold`}>{p.ticker}</td><td className={td}>{shortDate(p.latest_date)}</td><td className={td}>{p.rows}</td></tr>
                  ))}
                </tbody>
              </table>
            </Section>
          </div>
        </>
      )}
    </div>
  );
}
