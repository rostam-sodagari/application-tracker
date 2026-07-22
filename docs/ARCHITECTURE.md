# Architecture

## Overview

The backend exposes one API, under `/api`, regardless of which mode it is running in. Every other part
of the system, meaning the frontend, the routers, and the home statistics, is written against this API
and against a small set of internal Python functions, never against Appwrite directly. Which mode is
active is chosen by a single environment variable, `BACKEND_MODE`, read once at startup in
`backend/app/config.py`.

### Local mode

Data lives in a SQLite file at `backend/data/app.db`, and CV files live on local disk under
`backend/data/cv_storage/<user_id>/`. Accounts, password hashes, and a signed session token are all
handled by this backend directly. Nothing outside this machine is involved, and nothing needs to be
configured beyond a session secret before the application can be used.

### Appwrite mode

Data lives in an Appwrite Cloud project's database and storage services, reached through an
administrator-scoped API key that only the backend holds. Accounts are Appwrite accounts, created
through open self-registration directly against Appwrite's own account service; login is verified by
asking Appwrite whether a submitted token is still valid for a real, current session. The browser has no
access to the API key and no way to reach Appwrite's database or storage services on its own.

## The dispatcher pattern

`backend/app/db.py` and `backend/app/auth.py` are not implementations. Each reads `BACKEND_MODE` and
re-exports the matching implementation's functions under the same names, so that a router, or the home
statistics endpoint, can call `db.add_application(...)` or depend on `auth.require_auth` without knowing
or caring which mode is active.

The two storage implementations, `backend/app/stores/local_store.py` and
`backend/app/stores/appwrite_store.py`, expose an identical set of function names and arguments: every
function takes the calling user's id as its first argument, and every function that reads, updates, or
deletes a specific row confirms it belongs to that user before proceeding, returning `None` rather than
revealing that a row belonging to someone else exists. `appwrite_store.py` additionally sets Appwrite
row and file permissions scoped to the owning user as a second layer of protection, though the primary
enforcement is the ownership check itself, since this backend always authenticates to Appwrite with an
administrator key that would otherwise bypass Appwrite's own permission system.

The two authentication implementations, `backend/app/auth_providers/local_auth.py` and
`backend/app/auth_providers/appwrite_auth.py`, both expose a `require_auth` FastAPI dependency returning
the calling user's id. Local mode additionally mounts its own registration, login, and logout endpoints,
only when local mode is active; Appwrite mode mounts none, since the frontend registers and logs in
directly against Appwrite's account service.

This means leaving Appwrite, adopting it, or supporting a third backend later involves changing or
adding one pair of files, not the application as a whole.

## Components

### backend/app

`main.py` sets up the FastAPI application, mounts the unauthenticated `public_config` router, mounts
local mode's registration endpoints when local mode is active, applies the `require_auth` dependency to
every other API router, and serves the built frontend with a fallback route so client-side routing
continues to work on a page refresh.

`config.py` loads environment variables, validates `BACKEND_MODE`, and exposes every setting either
mode needs as a typed value, including the local SMTP settings used for account verification email.

`constants.py` defines the application status values and which fields an application update may touch,
shared by both storage implementations so the set of valid values only exists in one place.

`email_sender.py` sends the local-mode verification email over SMTP. It is not used at all in Appwrite
mode, where Appwrite's own account service sends that email.

The `routers` directory contains one file per resource: `applications.py`, `cvs.py`, `home.py`,
`meta.py`, and `settings.py`, each a thin layer translating an HTTP request into a call to `db.py`, plus
`public_config.py`, the one unauthenticated route, which tells the frontend which backend mode is
active before anyone has logged in.

### backend/scripts

`init_appwrite_schema.py` creates the `applications`, `cv_versions`, and `settings` tables and the
`cv-storage` bucket in Appwrite mode, if they do not already exist. It can be run again safely after a
schema change, since it skips anything already in place.

`migrate_add_user_ownership.py` is a one-time script for a project that was using Appwrite mode before
multi-user support existed. It tags every existing row with the id of the account that created it, so
that account continues to see everything it created once ownership checks are enforced.

### frontend/src

`api/client.ts` is a small wrapper around `fetch` that attaches the current session token to every
request, regardless of which backend issued it. `api/publicConfig.ts` reads the one unauthenticated
endpoint that tells the frontend which mode is active.

The `auth` directory contains `appwriteAuth.ts`, a minimal Appwrite client exposing only the account
service, and `AuthContext.tsx`, which handles login, registration, logout, and session restoration for
whichever mode is active, so that every page past the login screen behaves identically regardless of
which backend issued the session. In Appwrite mode a short-lived JWT is minted at login and refreshed
every ten minutes, since Appwrite tokens expire after fifteen; in local mode a signed token issued at
login or registration is valid for thirty days.

The `theme` directory contains `ThemeContext.tsx`, which controls light and dark mode independently of
the operating system's own preference, persists the choice to `localStorage`, and is applied before the
first paint by a small inline script in `index.html` so there is no flash of the wrong theme.

The `pages` directory contains one file per route: `LoginPage.tsx` (login and registration, adapting its
messaging to the active mode), `VerifyEmailPage.tsx` (confirms an email verification link for either
mode), `HomePage.tsx`, `ApplicationsPage.tsx`, `CvsPage.tsx`, and `SettingsPage.tsx`.

The `components` directory contains shared interface pieces: `Modal`, `ConfirmDialog`, `StatusSelect`,
`StatTile`, `NavBar`, `ThemeToggle`, `RequireAuth` (redirects to the login page until `AuthContext`
reports a signed-in user), `VerificationBanner` (a reminder shown until the account's email is
verified), and the application form itself.

## Data model

The `applications` table holds company, role, source, job URL, location, remote type, a salary range,
the identifiers of the attached CV and cover letter, the date applied, status, a follow-up date, and
free-text notes. Status is one of Unknown, Draft Ready, Applied, Screening, Interview, Final Round,
Offer, Rejected, or Withdrawn. Every row carries the id of the account that owns it.

The `cv_versions` table holds a file identifier referring to a file in storage, the file name, and the
company the CV was tailored for, where known, also scoped to an owning account.

The `settings` table holds one row per account, the low and high ends of its configurable weekly
application goal, created with default values of five and ten the first time it is read.

Local mode additionally has a `users` table: email, a bcrypt password hash, and whether the address has
been verified. Appwrite mode has no equivalent table, since accounts are Appwrite's own.

An application's CV and cover letter fields refer to entries in `cv_versions` by file identifier. This
is resolved by matching in application code rather than enforced as a database-level relationship, since
neither SQLite as used here nor Appwrite's database provides a cross-table foreign key for this case.

## Example: loading the Applications page

The browser holds a session token, obtained at login or registration and attached to every request by
`api/client.ts`. When the Applications page loads, it requests a page of applications, optionally
filtered by status and a search keyword, through this token. The backend's `require_auth` dependency
resolves to whichever mode is active: in local mode, it checks the token's signature and expiry
directly; in Appwrite mode, it asks Appwrite whether the token is still valid for a real session. Once
the caller's id is known, the applications router calls `db.search_applications`, which the dispatcher
routes to either the SQLite query or the equivalent Appwrite query, scoped to that id, and returns a page
of results together with the total count. The browser receives ordinary JSON and has no awareness of
which storage backend produced it.
