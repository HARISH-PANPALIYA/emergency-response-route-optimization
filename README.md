# Intelligent Emergency Response and Route Optimization

Portfolio-grade emergency dispatch software with a C++ graph engine, pybind11 bridge, FastAPI business layer, Neon PostgreSQL persistence, and a React operations interface. Demo facilities, units, and roads are explicitly synthetic.

## Architecture

React calls FastAPI. FastAPI persists users, facilities, units, emergencies, assignments, roads, and history through SQLAlchemy/psycopg. Route computation stays in C++17: a manually implemented adjacency-list graph and priority-queue Dijkstra are exposed through pybind11. A single source-distance run from an incident compares all reachable units and facilities; Python does not reimplement Dijkstra.

The map is generated from persisted roads. Blocked roads are passed into the C++ graph and ignored by Dijkstra. Primary and alternative routes are returned and the React SVG highlights the exact returned node-to-node segments.

## Features

- JWT authentication with bcrypt password hashing and backend-enforced USER/ADMIN roles
- Emergency types MEDICAL, FIRE, CRIME, and ACCIDENT
- Explicit lifecycle transitions with emergency history
- Automatic nearest reachable unit and government facility selection
- Persisted assignments and unit availability
- Admin facility, unit, and road management without destructive deletion
- Road blocking, unblocking, weight changes, and route recalculation
- Citizen reporting/history and admin control-room views

## Project layout

`cpp/` contains the routing library, tests, and bindings. `backend/` contains FastAPI, SQLAlchemy models, seed data, and API routes. `frontend/` contains the Vite React application. `render.yaml` describes the Render build and start commands.

## Local setup

Use Python 3.12 on Windows, install CMake and a C++17 compiler, then:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cmake -S . -B build -D CMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Create a local `.env` or `.env.local` from `.env.example`. `DATABASE_URL` is required and must point to PostgreSQL; the application intentionally does not fall back to SQLite or in-memory state. Set `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `FRONTEND_URL`, and optionally `CORS_ORIGINS`. Never commit either environment file.

Start the backend and frontend:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd ..\frontend
npm install
npm run dev
```

The backend creates missing tables and idempotently seeds the synthetic facilities, units, and roads. `backend/schema.sql` is the human-readable reference schema; runtime initialization currently uses SQLAlchemy `create_all`.

## Deployment

Neon PostgreSQL supplies `DATABASE_URL`. Render uses Python 3.12.10 from `runtime.txt`/`PYTHON_VERSION`, installs backend dependencies, discovers pybind11 through `python -m pybind11 --cmakedir`, builds the C++ extension with Linux CMake/GCC, and starts FastAPI on `0.0.0.0:$PORT`. Configure `DATABASE_URL`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `FRONTEND_URL` in Render; add `CORS_ORIGINS` only when more than one browser origin is required. Vercel builds `frontend` with `npm run build`; set `VITE_API_URL` to the Render HTTPS URL. No Docker image is required.

## Testing

```powershell
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
python -m pip check
cd frontend
npm run build
```

The integration workflow should cover registration/login, admin authorization, emergency creation, one-source auto-assignment, facility selection, road block/unblock, route recalculation, resolution, unit release, restart persistence, and history records.

## Complexity and limitations

For `V` graph nodes and `E` edges, Dijkstra is `O((V+E) log V)` with an adjacency list and binary heap. The same distance vector supports multiple candidate comparisons. The current project uses SQLAlchemy table creation rather than Alembic migrations, stores access tokens in browser local storage, and uses a synthetic fixed 36-node graph. Production hardening should add migrations, browser-level tests, and a hardened cookie/session strategy.
