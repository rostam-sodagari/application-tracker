# Security model

## Authentication

### Local mode

- **Passwords are hashed with bcrypt** before storage (`backend/app/auth_providers/local_auth.py`) and
  never kept or logged in plain form.
- **Sessions are a signed, stateless token**, produced with `itsdangerous` and a server-held secret
  (`LOCAL_SESSION_SECRET`). The token carries the account id and an issue time; it is valid for thirty
  days from issue and requires no server-side session store, since its own signature is what is
  verified on each request.
- **Login is rate-limited** per client IP: five attempts within a fifteen-minute window, held in memory.
  This is a basic brute-force deterrent, not a substitute for a strong password.
- **Email verification is optional and non-blocking.** If no SMTP provider is configured, a newly
  registered account is marked verified immediately, since there would be no way to ever complete a
  verification link. If one is configured, a signed, time-limited link (48 hours) is emailed on
  registration; following it marks the account verified. An unverified account can sign in and use the
  application normally; a dismissible reminder is shown in the interface until the address is confirmed,
  rather than the account being locked out, since a self-hosted install with an unreliable or
  intermittently configured mail server should not be able to lock its own owner out of their data.

### Appwrite mode

- **Credential storage is entirely Appwrite's responsibility.** Accounts are created directly against
  Appwrite's account service by the frontend; this application never receives, stores, hashes, or logs a
  password. Appwrite also owns its own login rate-limiting and brute-force protection.
- **Every `/api/*` request is independently verified**, not just the initial login. The frontend attaches
  a short-lived Appwrite JWT (`Authorization: Bearer <jwt>`, minted via `account.createJWT()` and
  refreshed every 10 minutes — Appwrite JWTs expire after 15) to each request. The backend's
  `require_auth` dependency (`backend/app/auth_providers/appwrite_auth.py`) confirms the JWT is still
  valid by calling Appwrite's `account.get()` scoped to it. No API key or other secret is involved in
  this check — the JWT itself is the proof of identity.
- **A 30-second in-memory cache** on the backend avoids re-verifying the same token against Appwrite for
  every single request in a short burst (e.g. one page load firing several API calls at once). This is
  purely a latency optimization: the cache TTL is far shorter than the JWT's own 15-minute lifetime, so
  it never extends how long an expired or revoked token would be honored.
- **Email verification uses Appwrite's own account service.** The frontend calls
  `account.createEmailVerification()` after registration and on request, and completes the process with
  `account.updateEmailVerification()` when a link is followed. Appwrite sends and validates the
  verification email itself; this backend is not involved and never sees the verification secret. As in
  local mode, an unverified account can still sign in and use the application.

#### Trade-off: continuous Appwrite dependency

Because verification happens per-request against Appwrite rather than via a session issued once at
login, **Appwrite mode needs Appwrite reachable continuously, not just at sign-in.** If Appwrite Cloud is
unreachable, the application is unusable in this mode until it is back — there is no local fallback
session. This was a deliberate choice: it means a revoked or expired Appwrite session is rejected on the
very next request everywhere, with no window where a locally cached session would still be honored. If
Appwrite's uptime becomes a practical problem, `backend/app/auth_providers/appwrite_auth.py` is the one
place that would need to change, or local mode can be used instead.

## Multi-user data isolation

Every application, CV, and settings row carries the id of the account that owns it. Both storage
implementations enforce the same rule, in application code, independent of which is active:

- Listing and searching filter to the caller's own rows only.
- Reading, updating, or deleting a specific row first confirms it belongs to the caller. If it does not,
  either because it belongs to someone else or does not exist at all, the response is an ordinary
  not-found, never a message that distinguishes "not yours" from "does not exist" — an attacker probing
  ids learns nothing either way.
- In Appwrite mode, each row and file additionally carries Appwrite permissions scoped to its owning
  account, as a second layer. This is defense in depth rather than the primary boundary, since this
  backend always authenticates to Appwrite with an administrator API key that would otherwise bypass any
  per-row permission; the ownership check described above is what actually enforces isolation.

This was verified directly, in both modes, before multi-user support was considered complete: a second
account cannot list, read, or delete a first account's applications or CVs, and receives its own default
settings rather than the first account's.

## Data access (Appwrite mode)

- **All application data is reached only through a single admin-scoped Appwrite API key**, held in
  `backend/.env` as `APPWRITE_API_KEY` and used exclusively by `backend/app/stores/appwrite_store.py`.
  This key is a genuine secret and must never be committed, logged, or exposed to the browser.
- **The browser never holds Appwrite data-plane credentials.** It only ever calls this backend's own
  `/api/*` routes; Appwrite's TablesDB and Storage APIs are not reachable from client-side code at all.
- **CV and cover-letter downloads** (`GET /cvs/open/{file_id}`) proxy the file through this backend
  rather than redirecting to a direct Appwrite Storage URL, and require the same per-request
  verification, plus the same ownership check, as every other route — there is no unauthenticated path
  to any stored file.

## What changing backends would involve

Because both integration points are isolated to one pair of files each:

- **Auth only**: add or change an implementation under `backend/app/auth_providers/`, matching the
  `require_auth` shape. `backend/app/auth.py` is where the new implementation gets selected.
- **Data only**: add or change an implementation under `backend/app/stores/`, matching the existing
  function names (`add_application`, `list_applications`, `upload_cv_file`, …). No router or frontend
  page needs to change, since they all call these functions, not Appwrite or SQLite directly.
- **Both**: do both of the above. Still no changes required to `routers/`, `frontend/src/pages/`, or
  `frontend/src/components/` — they are written against this backend's own API contract.

## Secrets checklist

| Value | Where it lives | Secret? |
|---|---|---|
| `LOCAL_SESSION_SECRET` | `backend/.env` (local mode) | **Yes** |
| `SMTP_PASSWORD` | `backend/.env` (local mode, optional) | **Yes** |
| `APPWRITE_ENDPOINT` / `APPWRITE_PROJECT_ID` | `backend/.env`, `frontend/.env.local` (Appwrite mode) | No |
| `APPWRITE_API_KEY` | `backend/.env` only (Appwrite mode) | **Yes** — full data read/write access |
| Account passwords | Bcrypt hash in local SQLite, or Appwrite's own account service | **Yes** — never kept in plain form by this application |

All `.env` files are gitignored at the repository root (`.gitignore`). Never paste a secret value
anywhere outside a `.env` file — not in chat, not in a commit, not in a log line.
