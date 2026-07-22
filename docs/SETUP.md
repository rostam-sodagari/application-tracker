# Setup

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
