import { useState } from "react";
import type { AssetType } from "../api";
import { price, shortDate } from "../format";

export interface Point {
  date: string;
  close: number;
}

// Dependency-free SVG line chart of closing prices.
export default function Chart({ points, type }: { points: Point[]; type: AssetType }) {
  const [hover, setHover] = useState<number | null>(null);
  if (points.length < 2) return <p className="text-sm text-slate-500">Not enough price history to draw a chart.</p>;

  const W = 640, H = 240, PX = 8, PT = 14, PB = 14;
  const closes = points.map((p) => p.close);
  const min = Math.min(...closes), max = Math.max(...closes);
  const x = (i: number) => PX + (i / (points.length - 1)) * (W - 2 * PX);
  const y = (v: number) => PT + (1 - (v - min) / (max - min || 1)) * (H - PT - PB);
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.close).toFixed(1)}`).join(" ");
  const area = `${line} L${x(points.length - 1).toFixed(1)},${H - PB} L${x(0).toFixed(1)},${H - PB} Z`;

  const shown = hover ?? points.length - 1;
  const p = points[shown];

  return (
    <div>
      <p className="mb-2 text-sm text-slate-600">
        <span className="font-bold text-slate-900">{price(p.close, type)}</span>{" "}
        <span className="text-slate-400">on {shortDate(p.date)}</span>
        <span className="ml-3 text-xs text-slate-400">
          range {price(min, type)} – {price(max, type)}
        </span>
      </p>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full touch-none select-none"
        role="img"
        aria-label="Closing price history"
        onPointerMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          const i = Math.round(((e.clientX - r.left) / r.width) * (points.length - 1));
          setHover(Math.max(0, Math.min(points.length - 1, i)));
        }}
        onPointerLeave={() => setHover(null)}
      >
        <defs>
          <linearGradient id="fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#fill)" />
        <path d={line} fill="none" stroke="#4f46e5" strokeWidth="2" strokeLinejoin="round" />
        <line x1={x(shown)} x2={x(shown)} y1={PT} y2={H - PB} stroke="#a5b4fc" strokeDasharray="4 4" />
        <circle cx={x(shown)} cy={y(p.close)} r="4.5" fill="#d946ef" stroke="white" strokeWidth="2" />
      </svg>
      <div className="mt-1 flex justify-between text-xs text-slate-400">
        <span>{shortDate(points[0].date)}</span>
        <span>{shortDate(points[points.length - 1].date)}</span>
      </div>
    </div>
  );
}
