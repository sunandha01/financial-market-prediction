import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  useApi, type ForecastResponse, type HistoryResponse, type MetricsResponse,
} from "../api";
import { ErrorBox, Loading } from "../components/ApiState";
import Chart from "../components/Chart";
import Flags from "../components/Flags";
import { DIRECTION, pct, pctPlain, price, shortDate } from "../format";

const RANGES = [{ label: "3M", rows: 63 }, { label: "1Y", rows: 252 }, { label: "2Y", rows: 500 }];

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-indigo-100 sm:p-6">
      <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-indigo-600">{title}</h2>
      {children}
    </section>
  );
}

function Metrics({ m }: { m: MetricsResponse }) {
  const x = m.metrics;
  const head = "px-2 py-2 text-left text-xs font-semibold text-slate-400";
  const cell = "px-2 py-2";
  return (
    <>
      <p className="mb-3 text-sm text-slate-600">
        Saved model: <strong>{m.model_name.replace("_", " ")}</strong>. Scores are averages over 5 walk-forward test
        windows, next to the two naive baselines.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px] text-sm">
          <thead>
            <tr>
              <th className={head}></th>
              <th className={head}>Model</th>
              <th className={head}>Average-return baseline</th>
              <th className={head}>Majority-direction baseline</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            <tr>
              <td className={`${cell} text-slate-500`}>Direction accuracy <span className="text-slate-400">(50% = coin flip)</span></td>
              <td className={`${cell} font-bold`}>{pctPlain(x.dir_acc)}</td>
              <td className={cell}>{pctPlain(x.baseline_mean_dir_acc)}</td>
              <td className={cell}>{pctPlain(x.baseline_majority_sign_dir_acc)}</td>
            </tr>
            <tr>
              <td className={`${cell} text-slate-500`}>Typical error (RMSE) <span className="text-slate-400">(lower is better)</span></td>
              <td className={`${cell} font-bold`}>{pctPlain(x.rmse, 2)}</td>
              <td className={cell}>{pctPlain(x.baseline_mean_rmse, 2)}</td>
              <td className={`${cell} text-slate-300`}>—</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div className="mt-4"><Flags rmse={x.beats_baseline_mean_rmse} direction={x.beats_both_direction_baselines} /></div>
      <p className="mt-3 text-xs text-slate-500">{m.note}</p>
      <p className="mt-1 text-xs text-slate-500">
        Not sure what these mean? See <Link to="/learn/mae-vs-direction" className="font-semibold text-indigo-600 underline">MAE vs direction accuracy</Link>.
      </p>
    </>
  );
}

export default function Asset() {
  const { ticker = "" } = useParams(); // router decodes GC%3DF -> GC=F
  const enc = encodeURIComponent(ticker);
  const forecast = useApi<ForecastResponse>(`/assets/${enc}/forecast`);
  const history = useApi<HistoryResponse>(`/assets/${enc}/history?limit=500`);
  const metrics = useApi<MetricsResponse>(`/assets/${enc}/metrics`);
  const [range, setRange] = useState(1);

  const f = forecast.data;
  const type = f?.asset_type ?? history.data?.asset_type ?? metrics.data?.asset_type ?? "fx";
  const name = f?.display_name ?? history.data?.display_name ?? ticker;
  const rows = history.data?.rows.slice(-RANGES[range].rows) ?? [];

  return (
    <div className="space-y-5">
      <Link to="/" className="text-sm font-semibold text-indigo-600 hover:underline">← All markets</Link>
      <div>
        <h1 className="text-2xl font-extrabold sm:text-3xl">{name}</h1>
        <p className="text-sm text-slate-500">
          {ticker}
          {type === "futures" && " · COMEX futures, not MCX spot"}
        </p>
      </div>

      <Card title="7-day forecast">
        {forecast.loading && <Loading />}
        {forecast.error && <ErrorBox error={forecast.error} retry={forecast.retry} />}
        {f && (
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <p className={`text-4xl font-extrabold ${DIRECTION[f.direction].text}`}>{pct(f.pred_return_7d)}</p>
              <p className="mt-1">
                <span className={`rounded-full px-2.5 py-0.5 text-sm font-bold ${DIRECTION[f.direction].chip}`}>
                  {DIRECTION[f.direction].arrow} {DIRECTION[f.direction].label}
                </span>
              </p>
              <dl className="mt-4 grid grid-cols-2 gap-y-1 text-sm">
                <dt className="text-slate-400">Last close</dt>
                <dd className="font-semibold">{price(f.last_close, f.asset_type)}</dd>
                <dt className="text-slate-400">As of</dt>
                <dd className="font-semibold">{shortDate(f.as_of)}</dd>
                <dt className="text-slate-400">Model</dt>
                <dd className="font-semibold">{f.model_name.replace("_", " ")}</dd>
                <dt className="text-slate-400">Horizon</dt>
                <dd className="font-semibold">7 trading days</dd>
              </dl>
            </div>
            <div>
              <Flags rmse={f.beats_baseline_rmse} direction={f.beats_baseline_direction} />
              <p className="mt-3 text-xs text-slate-500">{f.disclaimer}</p>
            </div>
          </div>
        )}
      </Card>

      <Card title="Price history (daily close)">
        <div className="mb-3 flex gap-1.5">
          {RANGES.map((r, i) => (
            <button
              key={r.label}
              onClick={() => setRange(i)}
              className={`rounded-full px-3 py-1 text-xs font-bold ${
                i === range ? "bg-indigo-600 text-white" : "bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
        {history.loading && <Loading />}
        {history.error && <ErrorBox error={history.error} retry={history.retry} />}
        {history.data && <Chart points={rows.map((r) => ({ date: r.date, close: r.close }))} type={type} />}
      </Card>

      <Card title="How the model scored">
        {metrics.loading && <Loading />}
        {metrics.error && <ErrorBox error={metrics.error} retry={metrics.retry} />}
        {metrics.data && <Metrics m={metrics.data} />}
      </Card>
    </div>
  );
}
