import type { AssetType } from "./api";

/** 0.00126 -> "+0.126%". Three decimals: 7-day forecasts here are tiny. */
export function pct(value: number): string {
  const s = (value * 100).toFixed(3);
  return Number(s) === 0 ? "0.000%" : `${value > 0 ? "+" : ""}${s}%`;
}

export function pctPlain(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function price(value: number, type: AssetType): string {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: type === "fx" ? 4 : 2,
    maximumFractionDigits: type === "fx" ? 4 : 2,
  });
}

export function shortDate(iso: string): string {
  return new Date(`${iso.slice(0, 10)}T00:00:00`).toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  });
}

export function dateTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" }) : "—";
}

export const DIRECTION = {
  up: { label: "Up", arrow: "▲", text: "text-emerald-600", chip: "bg-emerald-100 text-emerald-700" },
  down: { label: "Down", arrow: "▼", text: "text-rose-600", chip: "bg-rose-100 text-rose-700" },
  flat: { label: "Flat", arrow: "■", text: "text-slate-500", chip: "bg-slate-100 text-slate-600" },
} as const;

// Plain-language reading of the two baseline flags stored with each forecast.
export const rmseText = (beats: boolean) =>
  beats ? "Beats the average-return baseline" : "Does not beat the average-return baseline";
export const directionText = (beats: boolean) =>
  beats ? "Beats both naive direction baselines" : "Does not beat the naive direction baselines";
