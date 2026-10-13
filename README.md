# LearnPcode

A connected Python and DSA learning application: scroll through a lesson, step through its procedural visual, write actual Python in a browser worker, ask your local Ollama mentor for guidance, and keep personal practice history in Django.

**Rename it:** edit `shared/project.json`. Visual tokens and responsive styling are centralized in `frontend/src/styles.css`; procedural scene rendering is in `frontend/src/features/visualization/Scene.tsx`.

## What is implemented

- **24 original lessons and exercises**: 12 Python chapters and 12 DSA chapters. Each includes an objective, explanation, runnable example, output, demonstration, common mistake, constraints, examples, tests, progressive hints, and an explicitly retrieved reference answer.
- React/TypeScript/Vite/Tailwind interface, chapter URLs, normal scrolling, GSAP transitions, procedural React Three Fiber/Drei scenes, manual step controls, selectable textual equivalents, mobile/2D and reduced-motion views.
- Monaco syntax highlighting, a simple-editor alternative, Run/Stop/Reset/Submit, pre-supplied `input()` lines, stdout/error output, test results, draft buffering and backend saves.
- Lazy Pyodide module worker. Stop terminates it; the next run initializes a fresh runtime. Initialization has a 90-second limit; execution has an 8-second deadline. Output is capped. Exercise files are recreated for each run/test case.
- Django session authentication, CSRF protection, learner-owned drafts/attempts/progress/guidance events/conversations, and a dashboard with transparent revision rules.
- Two backend-mediated Ollama modes: explain a question and coach an attempt. Optional debounced hints, no overlapping client inference, stale-answer discard, limited context, timeouts, and honest unavailable states.
- Django admin, migration, idempotent seed command, readiness endpoint, backend tests, algorithm tests, and real browser-flow tests.

See [`VERIFICATION.md`](VERIFICATION.md) for actual results and remaining limitations.

## Prerequisites and tested versions

- Windows PowerShell 5.1, Node **24.17.0**, Python **3.13** (used for the backend virtual environment).
- PostgreSQL **16**; database credentials must be configured locally.
- Existing Ollama installation. The detected/tested model is **`qwen2.5:1.5b`**. Nothing installs Ollama or downloads a model.
- Internet access for first loading the pinned Pyodide **314.0.7** distribution. Monaco, geometry, and scene labels are bundled locally.
- Dependencies are resolved in `frontend/package-lock.json` and `backend/requirements.lock.txt`: React 19.3, R3F 9.8, Drei 10.7, Vite 8.3, Django 5.2.18, DRF 3.16.1, Monaco 0.57.0. Monaco's transitive DOMPurify is overridden to its patched 3.4.16 release.

Ports are **5174** for the frontend and **8001** for Django. Ports 5173 and 8000 were owned by other applications during setup and were left alone.

## Windows installation

Run these commands from the project directory (`E:\MSASC Projects\Python_Website` on this machine):

```powershell
py -3.13 -m venv backend\.venv
& .\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
npm --prefix frontend ci
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` locally. Do not put database passwords in chat or commit that file. Generate a secret with:

```powershell
& .\backend\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Set:

```dotenv
DJANGO_SECRET_KEY=your-generated-secret
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgresql://python_studio:URL_ENCODED_PASSWORD@localhost:5432/python_studio
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

Passwords containing `@`, `:`, `/`, `%`, or other URL-special characters must be percent-encoded in `DATABASE_URL`.

### Dedicated PostgreSQL database

Connect using your existing PostgreSQL administrator account. PostgreSQL's tools may not be on PATH:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U postgres -d postgres
```

Inside `psql`:

```sql
CREATE ROLE python_studio LOGIN;
\password python_studio
CREATE DATABASE python_studio OWNER python_studio;
\q
```

`\password` prompts privately. This creates a dedicated role/database; it does not alter other application databases. If either already exists, inspect it instead of rerunning the corresponding creation command.

Then migrate and seed:

```powershell
& .\backend\.venv\Scripts\python.exe backend\manage.py migrate
& .\backend\.venv\Scripts\python.exe backend\manage.py seed_content
& .\backend\.venv\Scripts\python.exe backend\manage.py createsuperuser
```

The superuser is optional and only needed for Django admin.

## Run

From the project directory:

```powershell
.\start-dev.ps1
```

The script verifies port ownership, reuses only identifiable project processes, applies migrations and seeds on fresh startup, and performs bounded frontend/backend checks. Ollama is checked separately; an unavailable mentor does not prevent the servers from starting. Logs are in `.logs/`.

Open **http://127.0.0.1:5174**. Admin is at **http://127.0.0.1:8001/admin/**. Readiness is visible at **http://127.0.0.1:5174/status**.

Alternatively, use separate terminals:

```powershell
# Terminal 1, project directory
& .\backend\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8001 --noreload
```

```powershell
# Terminal 2, project directory
npm --prefix frontend run dev
```

Use Ctrl+C in each terminal to stop those servers. To inspect detached processes without killing unrelated work:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 5174,8001 |
    Format-Table LocalAddress,LocalPort,OwningProcess
Get-CimInstance Win32_Process -Filter "ProcessId = REPLACE_WITH_REPORTED_PID" |
    Format-List ProcessId,Name,CommandLine
```

### Explicit SQLite preview

If you have not configured PostgreSQL credentials yet, an explicitly selected development fallback is available:

```powershell
.\start-dev.ps1 -UseSQLite
```

This uses `backend/development.sqlite3` and clearly reports `sqlite` on the status page. It still uses backend authentication and persistence; local storage is not the database. PostgreSQL is the normal default. SQLite and PostgreSQL contain separate accounts and progress; switching modes does not migrate learner data automatically.

### Ollama

```powershell
ollama list
# Start your existing Ollama desktop application, or if it is not already serving:
ollama serve
```

Keep `OLLAMA_MODEL` equal to an installed model name. If you change it, restart Django. The app never invokes `ollama pull` and never uses an external AI API key.

## How the connected flow works

1. `/api/curriculum/` supplies the chapter index. `/api/lessons/<id>/` loads one chapter and its exercise; reference answers and hint text are excluded.
2. An authored demonstration synchronizes its own code line and visual state. Editable DSA inputs generate bounded algorithm steps. It is **not a tracer for arbitrary learner code**.
3. Practice loads an account-owned draft. A debounced PUT saves it using a revision number, while an account-scoped browser buffer retains edits during interruptions. Conflicting server revisions are rejected.
4. Run/Submit send code to a dedicated Pyodide worker. Input comes from the visible input buffer. Function tests compare returned values; script tests compare captured stdout. Syntax/runtime errors are distinguished from wrong results.
5. Submit records browser-reported case summaries and code with the authenticated learner, lesson version, and guidance usage. The backend never executes learner code.
6. The mentor resolves exercise context on the backend and sends bounded code, feedback, and recent messages to the configured Ollama service. AI text is displayed separately from execution results.
7. Progress, attempts, hints, solution views, and conversations feed the dashboard. Completion is a self-marked study milestone. Revisit suggestions use latest failed attempts and cumulative guidance usage. No ML model is trained or claimed.

### Execution and assessment limits

- Browser-side tests are inspectable and their reported results can be modified by a client. This is a learning tool, **not a secure assessment judge**. Passing finite test cases does not prove correctness or algorithmic complexity for every input.
- Pyodide is a browser runtime, not a hardened sandbox for hostile programs. A worker isolates computation from the UI thread, but cannot promise an OS-level memory boundary. Only run code you intend to execute.
- Files are virtual. Fixtures `data.txt`, `empty.txt`, and `signed.txt` are recreated in `/home/pyodide/practice`; browser Python does not automatically access local computer files. This is workspace reset behavior, not a security filesystem jail.
- Input must be supplied before running. There is no interactive terminal prompt while execution is blocked. Missing input produces `EOFError`.
- Standard-library beginner code is supported. Native OS access, arbitrary installed desktop packages, subprocess-based tools, and server Python integrations may not be available.
- Monaco and 3D are lazy-loaded. Monaco's production chunk remains large (~700 KB compressed); a build size advisory is reported. The simple editor is available on all devices and default on small screens.
- The local backend uses a one-inference-per-process semaphore and in-process rate limiting. Multiple backend processes need a shared inference queue/rate-limit store before public scaling.

## Content maintenance and the missing book

Content source: `backend/learning/curriculum.py`. The idempotent `seed_content` command updates matching stable lesson/exercise IDs and creates missing ones. It does not delete learner records. **Seeding overwrites admin edits to seeded content fields**; make permanent seeded changes in the source, and bump lesson versions when changing test expectations.

```powershell
& .\backend\.venv\Scripts\python.exe backend\manage.py seed_content
```

Django admin provides lesson/exercise maintenance, including JSON demonstration/test fields. There is no separate admin dashboard.

**`Python_SQL_Logical_Interview_Questions(1).pdf` was not supplied or found. Its import is blocked.** All current exercises are explicitly original; no book contents, question IDs, or company provenance have been fabricated. When the actual PDF is supplied, extraction and manual validation must preserve its IDs/examples/constraints, flag ambiguities, omit SQL, and add verified reference answers/tests before seeding. No unverified PDF importer is presented as complete.

Data Science and ML teaching tracks are future scope, with no empty navigation links.

## Verification commands

### Backend tests

```powershell
# Explicit SQLite unit/integration run (test DB is separate from development data)
$env:DJANGO_DEBUG = "true"
$env:USE_SQLITE = "true"
& .\backend\.venv\Scripts\python.exe backend\manage.py test learning --verbosity 2
```

For PostgreSQL tests, set `USE_SQLITE=false` and use a **dedicated test database role with CREATEDB permission**. Django creates/destroys a `test_...` database; do not point automated tests at an unrelated role or service. PostgreSQL verification during implementation used an isolated temporary cluster on port 55432, not the existing port-5432 server.

### Frontend and browser checks

```powershell
npm --prefix frontend run build
npm --prefix frontend test
# Ensure the chosen development DB is migrated and seeded first.
npm --prefix frontend run test:e2e
```

Playwright uses installed Google Chrome. Set its `channel` in `frontend/playwright.config.ts` to `msedge` if only Edge is available. Browser tests start bounded project servers and use SQLite by default. Set `USE_SQLITE=false` and `DATABASE_URL` to run them against a dedicated PostgreSQL database. They create test learner accounts in that database. The live-mentor test expects the configured local model to be available; a failure is not replaced with a mocked success.

By default tests refuse occupied server ports. After checking ownership, set `$env:REUSE_DEV_SERVERS="true"` to reuse this project's already running servers. Those servers retain their existing environment/database settings.

Screenshots and failure traces are written to `frontend/test-results/` (ignored). Unit tests cover algorithm edge cases; backend tests cover CSRF, persistence, ownership, validation, unavailable mentor behavior, seeding, and authored content. Browser tests exercise real Pyodide, not canned output.

## Deploying to Vercel

The repository ships a `vercel.json` that uses [Vercel Services](https://vercel.com/docs/services) to build both applications as one deployment on one domain:

- `frontend/` builds to `frontend/dist` and serves every non-API path, including client-side routes such as `/learn/<slug>` and `/status`.
- `backend/` runs the Django WSGI app as a Vercel Function. `/api/*`, `/admin/*`, and `/static/*` are routed to it, so requests stay same-origin and the browser keeps its session cookie and CSRF token.

### Required project settings

Set the project Framework to **Services** in *Settings → Build and Deployment*. A project builds as services only when that is selected **and** `vercel.json` contains a `services` key. The frontend service pins Node from `frontend/package.json`; the backend service pins Python from `backend/.python-version`.

### Required environment variables

| Variable | Value |
| --- | --- |
| `DJANGO_SECRET_KEY` | A long random secret. |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | e.g. `.vercel.app`, plus any custom domain |
| `DATABASE_URL` | PostgreSQL URL including `?sslmode=require` |
| `DJANGO_SECURE_COOKIES` | `true` |
| `DJANGO_BEHIND_PROXY` | `true` |

Optional: `DJANGO_CSRF_TRUSTED_ORIGINS` (only when an extra custom domain is added; same-origin requests need no entry), `OLLAMA_BASE_URL`, and `OLLAMA_MODEL`.

### Deploy and first-time setup

Link the project, add the variables, and deploy:

```powershell
vercel link --yes --project <project-name>
vercel env add DJANGO_SECRET_KEY production
# repeat for every variable above, or set them in the project dashboard
vercel deploy --prod
```

Vercel installs `backend/requirements.txt`, runs `collectstatic`, and serves the collected admin/static files. It never runs migrations or seeding. Do those once against the hosted database from this project directory:

```powershell
$env:DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"
& .\backend\.venv\Scripts\python.exe backend\manage.py migrate
& .\backend\.venv\Scripts\python.exe backend\manage.py seed_content
& .\backend\.venv\Scripts\python.exe backend\manage.py createsuperuser
```

### Vercel differences

- Browser Python execution uses Pyodide, so it is unaffected by hosting.
- The mentor cannot reach `localhost:11434` from Vercel. Readiness reports Ollama as unavailable and the mentor shows its honest unavailable state until `OLLAMA_BASE_URL` points at a publicly reachable instance.
- Functions have a maximum duration (60 seconds on Hobby), and each function instance is ephemeral, so the in-process inference semaphore and rate limiting described below do not coordinate across instances.

## Hosting note

No infrastructure is deployed or purchased by this repository. `localhost:11434` works when Django and Ollama run on the same local machine. For public hosting, **the deployed backend** must be able to reach a hosted Ollama instance; visitors do not need Ollama installed.

Before hosting, configure HTTPS, a private database, a strong secret, secure cookies, permitted hosts/origins, static files, and same-origin `/api` routing. The Vite development proxy is not a production web server. Use a supported Django deployment server and reverse proxy; `npm run build` emits the frontend to `frontend/dist`. Review resource limits and shared inference coordination for the intended load. This release is not claimed to be production-ready.
