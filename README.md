# Sheetify Studio

Sheetify Studio is a multi-tenant SaaS platform that lets teams upload, build, and share Streamlit applications without exposing a terminal. It combines a FastAPI control plane, Docker-based runners, and a modern Next.js dashboard so creators can iterate quickly while operators retain control.

## Stack

- **Backend** – FastAPI + SQLAlchemy (async) with Celery workers and Redis for job orchestration.
- **Runner** – Docker sandbox orchestrated by a dedicated FastAPI service that builds tool images from a hardened Python 3.11 + Streamlit base and advertises routes through Traefik under `/t/<tool_id>`.
- **Frontend** – Next.js (TypeScript) with Tailwind CSS for the dashboard, build logs, and lifecycle controls.
- **Data stores** – PostgreSQL for persistent state, Redis for queues.

## Features

1. Email/password authentication with JWT sessions.
2. CRUD for Streamlit tools (name, description, owner) and version uploads via `.py` or `.zip` artifacts.
3. Packaging pipeline that normalises uploads into `app.py` + `requirements.txt`, infers dependencies when missing, and blocks dangerous imports such as `subprocess`, `os.system`, and `socket`.
4. Build jobs executed via Celery that produce container images from the trusted base, install requirements, and persist build logs + image references.
5. Runtime orchestration to start/stop Streamlit containers with `streamlit run app.py --server.headless true --server.baseUrlPath /t/<tool_id>`; Traefik publishes each tool under `/t/<tool_id>`.
6. Guardrails including import filtering and a base image entrypoint that drops outbound network traffic by default.
7. Next.js dashboard with a “Create Tool” wizard (paste or upload), build log viewer, start/stop controls, and shareable URLs.
8. A ready-made **CSV Explorer** template in `templates/csv_explorer/app.py` to seed new deployments.

## Getting started

1. **Build the sandbox base image** (required for the runner to layer user code):
   ```bash
   docker build -f runner/base/Dockerfile -t sheetify-base:latest .
   ```
2. **Launch the stack**:
   ```bash
   docker compose up --build
   ```
   This brings up PostgreSQL, Redis, the FastAPI API, Celery worker, runner service, Next.js dashboard, and Traefik proxy.
3. **Access the dashboard** at [http://localhost](http://localhost). The backend API is proxied under `/api` by Traefik.

## API surface

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/v1/auth/register` | Create a new user. |
| `POST` | `/v1/auth/token` | Obtain a JWT access token. |
| `POST` | `/v1/tools` | Create a tool. |
| `GET` | `/v1/tools/{id}` | Fetch tool details, versions, builds, and runs. |
| `POST` | `/v1/tools/{id}/versions` | Upload a new version (`.py` or `.zip`). |
| `POST` | `/v1/tools/{id}/build` | Queue a build for a version. |
| `POST` | `/v1/tools/{id}/run` | Start the latest build in the sandbox. |
| `POST` | `/v1/tools/{id}/stop` | Stop and remove the running container. |

## Frontend flows

- **Create Tool** – authenticate, complete the wizard (paste code or upload archive), and you’ll be redirected to the tool detail view.
- **Build & Run** – from the tool page you can queue builds, watch logs update in near real-time, start/stop the Streamlit container, and copy the share link exposed at `/t/<tool_id>`.

## Development notes

- The Celery worker and runner communicate over HTTP; update `RUNNER_URL` in `docker-compose.yml` if you change hostnames.
- Runner containers inherit security controls (no-new-privileges, drop `NET_RAW`, outbound firewall) from the hardened base image.
- Tool uploads are scanned for banned imports before storage.
- Extend the template catalog by dropping additional apps into `templates/`.

## Testing

Run the backend unit test suite with `pytest` from the repository root:

```bash
pytest
```

If you add JavaScript/TypeScript tests in the frontend, execute them with the appropriate `npm` script from the `frontend/` directory (for example, `npm test`).

Happy building!
