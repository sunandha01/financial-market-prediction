# Phase 10 — Authentication report

Scope: one admin, no user table, no OAuth. Public pages stay public; only `/admin` and the `POST /admin/*` routes need the token.

## Design

- **Credential:** the existing `ADMIN_TOKEN` from the server's `.env` (documented in `.env.example`, no real value committed). Empty = admin disabled. I chose the token option you allowed instead of a username/password pair: it needs no password hashing or session store, and there is only one admin.
- **Login (`/login`):** the form sends the token to a new `GET /admin/check` (header `X-Admin-Token`). Only if the API accepts it is the token kept, in **`sessionStorage`** (this tab only; cleared on logout or when the tab closes; never `localStorage`, never in a URL).
- **Guard:** `/admin` renders only when a token is held, otherwise redirects to `/login` (and returns to `/admin` after login). On opening `/admin` the stored token is re-verified, so a token that no longer matches the server (rotated `ADMIN_TOKEN`) is dropped and you are sent back to `/login`. Any 401 from an admin action also logs out.
- **Admin page:** **Refresh prices** → `POST /admin/refresh`; **Write forecasts** → `POST /admin/write-forecasts`, both with `X-Admin-Token`. Each starts the existing job and then polls `/status` until a new run finishes, showing its `ok`/`error` message. **Retrain** is disabled ("not in this phase"). **Log out** clears the token. The nav shows "Log in" when logged out and "Admin" when logged in.

## API changes (`api/main.py`)

| Change | Why |
|---|---|
| `GET /admin/check` (token required) → `{"ok": true}` | lets the login form verify a token without starting a job |
| token compared as bytes with `hmac.compare_digest` | the previous `str` comparison raised on a non-ASCII header value, which would have been a 500; now a clean 401 |
| failed-attempt limit: 10 wrong tokens per client address per 60 s → `429`, even for the right token until the window passes | stops trivial guessing of a weak token; in-memory, resets on restart |

Status codes for admin routes: 503 admin disabled (no `ADMIN_TOKEN`), 401 missing/wrong token, 429 too many failures, 409 job already running, 202 job started, 501 retrain stub.

## Verified

Against a throwaway token on a test API (port 8001), in the browser pane, with the real database:

- Logged out, `/admin` → redirected to `/login`.
- Wrong token → "That token wasn't accepted.", nothing stored.
- Right token → `/admin` with the two job buttons and a disabled Retrain button; token present in `sessionStorage`, `localStorage` empty.
- **Write forecasts ×2 and Refresh prices ×1 from the UI (plus one earlier run): `forecasts` stayed at 5 rows, 0 duplicate `(ticker, as_of)` keys, `ohlcv` stayed at 9917 rows.** Each panel showed its own job's `ok` message.
- Log out → token cleared, back on `/login`, nav shows "Log in". A planted stale token was rejected and cleared on opening `/admin`.
- Markets, asset page, Learn and Status all load with no login.
- `tests/test_api.py` (adds `/admin/check`, non-ASCII header and throttle cases) and all earlier suites pass. `npm run build` passes.

A bug found and fixed during this test: the Admin page's job panel used a "still mounted" ref that React StrictMode's dev double-mount left permanently false, so the panel never updated after starting a job (the job itself ran). The ref was removed.

## Limits — read before Phase 11

- The token travels in a request header over plain HTTP on localhost. **Any deployment must use HTTPS**, otherwise the token can be read on the network.
- `sessionStorage` is readable by any script on the page, so an XSS bug would expose it. React escapes output and the site loads no third-party scripts, but there is no Content-Security-Policy yet.
- One shared secret: no per-person accounts, no audit of who ran what, no expiry (a token stays valid until `ADMIN_TOKEN` changes).
- The failed-attempt limiter is per process and per client address; behind a reverse proxy every client may appear as one address, so it would need the real client IP.
- No frontend automated tests; the login flow was checked by hand in the browser.
