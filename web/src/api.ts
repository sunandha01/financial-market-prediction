import { useEffect, useState } from "react";

// The API must be running (uvicorn api.main:app --reload). Override with VITE_API_URL.
export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.status = status; // undefined = could not reach the API at all
  }
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { signal });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new ApiError(`Can't reach the API at ${API_URL}.`);
  }
  if (!res.ok) {
    let detail = `The API answered with an error (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch { /* keep the generic message */ }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export function useApi<T>(path: string) {
  const [state, setState] = useState<{ data?: T; error?: ApiError; loading: boolean }>({ loading: true });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const ctrl = new AbortController();
    setState({ loading: true });
    apiGet<T>(path, ctrl.signal)
      .then((data) => setState({ data, loading: false }))
      .catch((e: Error) => {
        if (e.name === "AbortError") return;
        setState({ error: e instanceof ApiError ? e : new ApiError(String(e)), loading: false });
      });
    return () => ctrl.abort();
  }, [path, tick]);

  return { ...state, retry: () => setTick((t) => t + 1) };
}

// --- response shapes (see reports/phase8_api.md) ---

export type AssetType = "fx" | "futures";

export interface ForecastCore {
  as_of: string;
  pred_return_7d: number;
  direction: "up" | "down" | "flat";
  model_name: string;
  last_close: number;
  beats_baseline_rmse: boolean;
  beats_baseline_direction: boolean;
  created_at: string;
}

export interface AssetInfo {
  ticker: string;
  display_name: string;
  asset_type: AssetType;
}

export interface AssetsResponse {
  disclaimer: string;
  assets: (AssetInfo & { latest_forecast: ForecastCore | null })[];
}

export type ForecastResponse = AssetInfo & ForecastCore & { disclaimer: string };

export interface HistoryRow {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}
export type HistoryResponse = AssetInfo & { count: number; rows: HistoryRow[] };

export interface MetricsResponse extends AssetInfo {
  model_name: string;
  artifact_path: string;
  trained_at: string;
  note: string;
  metrics: {
    dir_acc: number;
    rmse: number;
    mae: number;
    r2: number;
    baseline_mean_rmse: number;
    baseline_mean_dir_acc: number;
    baseline_majority_sign_dir_acc: number;
    beats_baseline_mean_rmse: boolean;
    beats_both_direction_baselines: boolean;
  };
}

export interface StatusResponse {
  jobs: { job_name: string; status: string; started_at: string; finished_at: string | null; message: string | null }[];
  forecasts: { ticker: string; latest_as_of: string }[];
  prices: { ticker: string; latest_date: string; rows: number }[];
}
