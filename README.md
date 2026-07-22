# Application Tracker

A job application tracker for one or more accounts. It records each application, keeps the CV and
cover letter sent for it, tracks status through to an offer, and keeps every tailored CV in one place.

The backend is written in FastAPI. The frontend is a React application built with Vite, TypeScript,
and Tailwind CSS. The backend supports two interchangeable storage and authentication modes, chosen by
a single environment variable:

- **Local mode**, the default, needs no external account. Data is stored in a SQLite file and CV files
  on local disk, both under `backend/data`. Accounts are created directly against this backend.
- **Appwrite mode** stores data and accounts in an Appwrite Cloud project instead, for anyone who wants
  managed hosting rather than a local file. The browser never communicates with Appwrite's data
  services directly, only with this backend's own API; Appwrite is used for its database, storage, and
  account services.

Every account, in either mode, only ever sees its own applications, CVs, and settings. The application
does not submit anything on a user's behalf. It reads and writes only its own data.

## Documentation

- [docs/SETUP.md](docs/SETUP.md) describes both setup paths, the environment variables each one reads,
  and how to run and deploy the application.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) explains how the two backend modes fit together and the
  reasoning behind the design.
- [docs/SECURITY.md](docs/SECURITY.md) describes the authentication, multi-user data isolation, and
  email verification model in detail.

## Quick start (local mode)

The prerequisites are Python 3.11 or later and Node 18 or later. No external account is required.

```
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and set `LOCAL_SESSION_SECRET` to a random value, for example the output of
`python -c "import secrets; print(secrets.token_hex(32))"`.

```
cd ../frontend
npm install
npm run build

cd ../backend
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`, register an account, and sign in. Setting up Appwrite mode instead, and
running the two together during frontend development, are both described in
[docs/SETUP.md](docs/SETUP.md).

## Project layout

The `backend` directory contains the FastAPI application. `app/stores` holds the local and Appwrite
storage implementations, `app/auth_providers` holds the local and Appwrite authentication
implementations, and `app/db.py`/`app/auth.py` are the thin dispatchers that select between them based
on `BACKEND_MODE`. The `frontend` directory contains the React application, which is built once and
then served by the backend. The `docs` directory contains the setup, architecture, and security
documentation.

## Features

Applications can be added, edited, and deleted, with company, role, source, posting URL, location,
remote type, salary range, a status, a follow-up date, and free-text notes. Status moves through Draft
Ready, Applied, Screening, Interview, Final Round, and then Offer, Rejected, or Withdrawn. A CV and
cover letter can be attached while creating or editing an application, uploading them in the same step;
every uploaded file is also kept on the CVs page, where it can be tagged with the company it was
tailored for and deleted, which also removes the underlying file from storage.

The Applications page supports keyword search, a status filter, and pagination. The home page shows
applications sent in the current week against a configurable weekly goal, response, interview, and
offer rates, a breakdown by status, and follow-ups that are due. The Settings page controls the weekly
goal. The interface supports both light and dark mode, toggled independently of the operating system's
own preference and remembered between visits.

Newly registered accounts are asked to verify their email address: through Appwrite's own verification
email in Appwrite mode, or through a configurable SMTP provider in local mode. An account remains usable
before verifying; a banner is shown as a reminder until it is confirmed.
