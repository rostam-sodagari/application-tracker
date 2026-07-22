# Setup

[README](../README.md) · Setup · [Architecture](ARCHITECTURE.md) · [Security](SECURITY.md)

The backend supports two modes, chosen by the `BACKEND_MODE` environment variable: `local` (the
default) and `appwrite`. Pick one before following the rest of this document. Both are described in
full below; local mode is the simpler starting point if unsure.

## Local mode

Local mode needs no external account. Data is stored in a SQLite file and CV files on local disk, both
under `backend/data`, created automatically on first run.

### Environment variables

The backend reads its configuration from `backend/.env`, copied from `backend/.env.example`.

| Variable | Secret | Purpose |
|---|---|---|
| BACKEND_MODE | No | Set to `local` |
| LOCAL_SESSION_SECRET | Yes | Signs session tokens and email verification links. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`. Without a real value, restarting the process invalidates every session |
| APP_BASE_URL | No | The origin the frontend is served from, used to build the link inside verification emails. Defaults to `http://localhost:8000` |

Email verification is optional and off by default. Leaving the following unset means newly registered
accounts are marked verified immediately, since a server with no mail provider configured has no way to
ever deliver a verification link.

| Variable | Secret | Purpose |
|---|---|---|
| SMTP_HOST | No | Mail server hostname. Leave unset to skip verification entirely |
| SMTP_PORT | No | Defaults to 587 |
| SMTP_USERNAME | No | Used for both authenticating to the mail server and, if `SMTP_FROM_EMAIL` is unset, as the sender address |
| SMTP_PASSWORD | Yes | |
| SMTP_USE_TLS | No | Defaults to true |
| SMTP_FROM_EMAIL | No | Sender address shown to recipients |

### Installing and running

```
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env`: set `BACKEND_MODE=local` and a real `LOCAL_SESSION_SECRET`.

```
cd ../frontend
npm install
npm run build

cd ../backend
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`, register an account, and sign in.

## Appwrite mode

Appwrite mode stores data and accounts in an Appwrite Cloud project instead of on local disk. Use it for
managed hosting, or to share the deployment's data across a browser and another device without setting
up a database yourself.

### Appwrite project

1. Create a project at cloud.appwrite.io. Note the project ID and the API endpoint, found under
   Settings and then General. Neither value is secret.
2. Under Auth and then Settings, confirm the Email/Password method is enabled and that self-registration
   is allowed, since Appwrite mode relies on open registration rather than a single pre-created account.
   If the console offers an option to require email verification before a session can be used, leave it
   off, so behavior matches local mode: an account is usable immediately, with a reminder banner shown
   in the interface until its address is confirmed.
3. Under Settings and then Platforms, add a Web platform for every origin the frontend will be served
   from, for example `http://localhost:5173` during development and the deployment's real origin in
   production. Appwrite rejects requests from an origin that is not registered here.
4. Under Overview, then Integrations, then API Keys, create a key with the following scopes:
   databases.read, databases.write, tables.read, tables.write, columns.read, columns.write,
   indexes.read, indexes.write, rows.read, rows.write, buckets.read, buckets.write, files.read, and
   files.write.

   Unlike the project ID and endpoint, this key is a secret. It authorizes full read and write access to
   the application's data and should never be committed to version control or shared.

   If this key will also be used by the tagged-release deploy workflow described below, add
   `functions.read` and `functions.write` to it as well; pushing a new code deployment to a Function is
   a separate permission from reading and writing application data, even once the Function itself
   already exists.
5. For production use, configure a custom SMTP provider under Messaging, rather than relying on Appwrite
   Cloud's own default sender for verification email, which is rate-limited.

### Environment variables

The backend reads its configuration from `backend/.env`, copied from `backend/.env.example`.

| Variable | Secret | Purpose |
|---|---|---|
| BACKEND_MODE | No | Set to `appwrite` |
| APPWRITE_ENDPOINT | No | The Appwrite API endpoint from step one above |
| APPWRITE_PROJECT_ID | No | The Appwrite project ID from step one above |
| APPWRITE_API_KEY | Yes | The key created in step four, used for all application data access |

The frontend reads its configuration from `frontend/.env.local`, copied from `frontend/.env.example`.

| Variable | Secret | Purpose |
|---|---|---|
| VITE_APPWRITE_ENDPOINT | No | The same endpoint as above, used for login, registration, and email verification |
| VITE_APPWRITE_PROJECT_ID | No | The same project ID as above |

Both frontend values end up in the built JavaScript bundle, which is expected and not a concern, since
neither is secret. Security depends on the Appwrite API key remaining on the server, not on keeping the
project ID hidden. These two values are only needed when building a frontend intended to run in
Appwrite mode; a deployment that only ever uses local mode can leave `frontend/.env.local` unset.

### Installing and initializing

```
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and fill in the four values described above, then run the schema setup script:

```
venv\Scripts\python scripts\init_appwrite_schema.py
```

This script creates the `applications`, `cv_versions`, and `settings` tables and the `cv-storage`
bucket if they do not already exist. It is safe to run again after a schema change; it will skip
anything that is already in place. The exact column definitions are in
`backend/scripts/init_appwrite_schema.py`.

```
cd ../frontend
npm install
copy .env.example .env.local
npm run build
```

If this Appwrite project already has application data from before multi-user support existed, run the
one-time ownership migration once, using the id of the account that created that data, found in the
Appwrite console under Auth and then Users:

```
cd ../backend
venv\Scripts\python scripts\migrate_add_user_ownership.py <ACCOUNT_USER_ID>
```

## Running locally

The application is run day to day with a single command, regardless of mode.

```
cd backend
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`. The frontend must be rebuilt with `npm run build` in the `frontend`
directory whenever it changes; the backend serves whatever is currently present in `frontend/dist`.

On macOS or Linux, replace the Windows-specific commands above with `python3 -m venv venv`,
`source venv/bin/activate && pip install -r requirements.txt`, and `cp` in place of `copy`.

### Active frontend development

While actively editing the interface, it is more convenient to run two processes instead of the single
command above.

```
cd backend && venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

```
cd frontend && npm run dev
```

The Vite development server proxies requests under `/api` and `/cvs` to the backend, configured in
`frontend/vite.config.ts`.

## Deploying

Any environment capable of running a Python process, including a container, is suitable: a virtual
private server, Fly.io, Render, Railway, or a personal server.

In local mode, `backend/data` must live on a persisted volume, since it holds the SQLite database and
every CV file; losing it loses all application data. In Appwrite mode there is no local database or
persisted volume to manage, since all data lives in Appwrite, but Appwrite Cloud must remain reachable
continuously, not only during login, for the reasons described in docs/SECURITY.md.

A reverse proxy that terminates TLS should sit in front of this backend in any real deployment. Caddy is
a reasonable choice, since it provisions HTTPS automatically once a domain name points at it.

Local mode's login rate limiting keys off the connecting client's IP address, as reported by Uvicorn.
When the reverse proxy runs on the same host as this backend, Uvicorn's default already trusts it and
this needs no further configuration. When the proxy runs elsewhere, for example a separate container on
a Docker network, pass `--forwarded-allow-ips` to Uvicorn with the proxy's actual address, so it reads
the real client IP from the `X-Forwarded-For` header the proxy sets rather than treating every request
as coming from the proxy itself. Skipping this in that kind of deployment does not stop the application
from working, but it does mean every visitor shares one rate-limiting bucket, so one person's failed
login attempts could temporarily lock out everyone else's.

### Deploying to Appwrite on a tagged release

`.github/workflows/deploy.yml` pushes a new code deployment to an Appwrite Function on every version
tag (`v1.2.3`) pushed to this repository, using Appwrite mode. This is only meaningful for Appwrite
mode: a Function's filesystem is not a persistent volume, so local mode's SQLite file and CV storage
would not survive a redeploy.

The Function itself is created once, manually, in the Appwrite console, the same way the Appwrite
project itself is set up above:

1. Under Functions, create a function with the Python runtime.
2. Set its build command to install this backend's dependencies, for example
   `pip install -r backend/requirements.txt`, and its start command to run the server, for example
   `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`, matching the archive layout the
   workflow uploads (`backend/` and `frontend/dist/` as sibling directories at the deployment's root).
3. Set the function's environment variables to the same `BACKEND_MODE=appwrite` values described
   above, plus `LOCAL_SESSION_SECRET` only if local mode is ever toggled on for testing.
4. Note the function's id, shown in the console.

Then add the following as repository secrets, under Settings and then Secrets and variables, then
Actions:

| Secret | Purpose |
|---|---|
| APPWRITE_ENDPOINT | The same endpoint used elsewhere |
| APPWRITE_PROJECT_ID | The same project id used elsewhere |
| APPWRITE_API_KEY | A key with `functions.read` and `functions.write` scope. Can be the same key used for application data, with those two scopes added, or a separate key dedicated to deployment |
| APPWRITE_FUNCTION_ID | The function id from step four above |

Pushing a tag, for example `git tag v1.0.0 && git push origin v1.0.0`, builds the frontend, packages it
with the backend, and activates the result as the function's new deployment. A deployment rejected with
a `missing scopes` error almost always means the key behind `APPWRITE_API_KEY` does not have
`functions.write` yet.
