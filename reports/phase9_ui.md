# Phase 9 — React dashboard report

Stack: React 19 + Vite + Tailwind CSS 4 + TypeScript, in `web/`. Light, mobile-first theme (indigo/violet/fuchsia accents on a pale gradient, white cards). No charting library: the price chart is a small SVG component. No forecast value is hardcoded anywhere; every number comes from the API. Tickers are URL-encoded (`GC=F` → `/assets/GC%3DF`).

Run: API on :8000 (`uvicorn api.main:app --reload`), then `cd web && npm install && npm run dev` → http://localhost:5173. `npm run build` type-checks and builds cleanly.

## Routes

| Route | Page | API calls |
|---|---|---|
| `/` | Markets: hero + five asset cards | `GET /assets` |
| `/assets/:ticker` | Asset detail | `GET /assets/{t}/forecast`, `/history?limit=500`, `/metrics` |
| `/learn` | Learn index (8 topics) | – |
| `/learn/:slug` | Learn topic | – |
| `/status` | Job runs, forecast dates, price freshness | `GET /status` |

Every page has the header (Markets / Learn / Status, "Experimental" badge) and a footer: experimental forecasts, not advice; gold/silver are COMEX futures, not MCX spot; link to the full disclaimer.

## Pages

- **Markets.** Five cards (USD/INR, EUR/USD, GBP/USD, Gold futures (COMEX), Silver futures (COMEX)). Each shows display name, ticker, an FX/Futures chip, the 7-day forecast as a signed percent with an Up/Down/Flat chip, last close, as-of date, model name, and two plain-text baseline notes from the stored flags: "Does not beat the average-return baseline" / "Beats …" and "Does not beat the naive direction baselines" / "Beats both naive direction baselines" (amber when not beating, green when beating). Live result: only GBP/USD shows the green direction note; all five show the amber error note. Gold shows **-0.022%**, matching `curl /assets/GC=F/forecast` (`-0.0223843…%`). A card with no stored forecast says so instead of showing a number.
- **Asset detail.** Big forecast percent with direction, last close, as-of, model, horizon, both baseline notes and the disclaimer; a daily-close line chart with 3M / 1Y / 2Y ranges and a hover/touch readout; a "How the model scored" table (direction accuracy and RMSE for the model vs the average-return and majority-direction baselines) with a link to the MAE-vs-direction Learn page and the API's optimism note. Each section loads and fails independently.
- **Learn.** Index of eight topics, each a short page with a "Next" link: Return vs price · The 7-day horizon · Direction and the naive baselines (states that GBP/USD is the only market that beat both direction baselines, and that no model beat the average-return baseline on error) · The five markets (FX vs COMEX futures) · Indicators (RSI, MACD, moving averages, Bollinger Bands, ATR, one paragraph each) · Walk-forward validation (why rows are never shuffled, the 5 folds and 7-day gap) · MAE vs direction accuracy · Disclaimer. No copy promises profit or accuracy.
- **Status.** Last run of each job (ok / error badge, start and finish times, message), latest forecast as-of per ticker, latest price date and row count per ticker.

## API-down and empty states

If the API is unreachable, the affected section shows "The forecast API is not reachable", the start command and a Try again button, with no numbers. A 404 from the API (nothing stored yet) shows the API's message in a neutral box. Verified by stopping the API, reloading, restarting it and clicking Try again.

## Checked

- `npm run build` (tsc + vite) passes.
- In the browser pane against the live API: Markets (five cards), Asset detail for `GC%3DF` (forecast, chart, metrics), Learn topic, Status, the API-down state and recovery, and a 375 px phone viewport (no horizontal overflow on `/assets/GC%3DF`, `/status`, `/learn`, `/learn/indicators`).
- No automated frontend tests were added.
