import { Link } from "react-router-dom";
import { useApi, type AssetsResponse } from "../api";
import { ErrorBox, Loading } from "../components/ApiState";
import Flags from "../components/Flags";
import { DIRECTION, pct, price, shortDate } from "../format";

type AssetCard = AssetsResponse["assets"][number];

function Card({ asset }: { asset: AssetCard }) {
  const f = asset.latest_forecast;
  const futures = asset.asset_type === "futures";
  return (
    <Link
      to={`/assets/${encodeURIComponent(asset.ticker)}`}
      className="group flex flex-col overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-indigo-100 transition hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className={`h-1.5 ${futures ? "bg-linear-to-r from-amber-400 to-orange-500" : "bg-linear-to-r from-sky-400 to-indigo-500"}`} />
      <div className="flex flex-1 flex-col gap-4 p-5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h2 className="font-bold leading-tight group-hover:text-indigo-700">{asset.display_name}</h2>
            <p className="text-xs text-slate-400">{asset.ticker}</p>
          </div>
          <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${
            futures ? "bg-amber-100 text-amber-700" : "bg-sky-100 text-sky-700"
          }`}>
            {futures ? "Futures" : "FX"}
          </span>
        </div>

        {f ? (
          <>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">7-day forecast</p>
              <p className="flex items-baseline gap-2">
                <span className={`text-3xl font-extrabold ${DIRECTION[f.direction].text}`}>{pct(f.pred_return_7d)}</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${DIRECTION[f.direction].chip}`}>
                  {DIRECTION[f.direction].arrow} {DIRECTION[f.direction].label}
                </span>
              </p>
            </div>
            <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-sm">
              <dt className="text-slate-400">Last close</dt>
              <dd className="text-right font-semibold">{price(f.last_close, asset.asset_type)}</dd>
              <dt className="text-slate-400">As of</dt>
              <dd className="text-right font-semibold">{shortDate(f.as_of)}</dd>
              <dt className="text-slate-400">Model</dt>
              <dd className="text-right font-semibold">{f.model_name.replace("_", " ")}</dd>
            </dl>
            <Flags rmse={f.beats_baseline_rmse} direction={f.beats_baseline_direction} />
          </>
        ) : (
          <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">
            No forecast stored for this market yet. Run the forecast job, then refresh.
          </p>
        )}
      </div>
    </Link>
  );
}

export default function Home() {
  const { data, error, loading, retry } = useApi<AssetsResponse>("/assets");
  return (
    <div>
      <section className="rounded-3xl bg-linear-to-br from-indigo-600 via-violet-600 to-fuchsia-600 p-6 text-white shadow-lg sm:p-8">
        <h1 className="text-2xl font-extrabold sm:text-3xl">7-day return forecasts for five markets</h1>
        <p className="mt-2 max-w-2xl text-indigo-50">
          A student project that tests whether simple machine-learning models can say anything useful about the next
          week's move. Every card shows how the forecast compares with naive baselines — read those notes first.
        </p>
        <p className="mt-3 text-sm font-semibold text-white/90">
          {data?.disclaimer ?? "Experimental forecast, not investment advice."}
        </p>
      </section>

      <div className="mt-6">
        {loading && <Loading label="Loading markets from the API…" />}
        {error && <ErrorBox error={error} retry={retry} />}
        {data && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data.assets.map((a) => <Card key={a.ticker} asset={a} />)}
            </div>
            <p className="mt-5 text-sm text-slate-500">
              New here? <Link to="/learn" className="font-semibold text-indigo-600 underline">Learn what these numbers mean</Link>.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
