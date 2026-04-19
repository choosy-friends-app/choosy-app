# Choosy App

A collaborative web application for group decision-making. It allows groups of users to propose plans, vote on options, and receive real-time notifications. Developed with Django as a project for the **Web Project** course (Bachelor's Degree in Computer Engineering, UdL 2025/26).

## Features

- User authentication and registration
- Group management with roles (Owner, Admin, Member)
- Invitation system with accept/reject functionality
- Plan proposals with option-based voting (upvote/downvote)
- Notification center with real-time counter
- History and archive of past plans
- Django admin panel

## Tech Stack

- **Backend**: Django 5.1+ (Python 3.12)
- **Database**: PostgreSQL 16 (Docker) / SQLite3 (local development)
- **Server**: Gunicorn (production)
- **Dependency Manager**: uv
- **Containers**: Docker + docker-compose

## Data Model

The model includes 6 entities with complex relationships:

- `Group` — User group with state and metadata
- `GroupMember` — User-group relationship with role and invitation status
- `PlanProposal` — Voting round with a timeframe
- `Plan` — Individual option within a proposal
- `Vote` — A member's vote for a plan
- `Notification` — Notifications for invitations, new plans, and decisions

## Run with Docker (Recommended)

### 1. Clone the repository

```bash
git clone https://github.com/choosy-friends-app/choosy-app.git
cd choosy-app
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set a secure `SECRET_KEY` for production. For local development, you can use the default values.

### 3. Start the application

```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`.

The command automatically runs migrations on startup.

### 4. (Optional) Create demo data

```bash
docker-compose exec web uv run python manage.py seed_demo_users
```

Creates users: `aleix`, `bru`, `eldejuneda`, `chileno` (password: `demo1234` for everyone).

## Run locally with uv

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Local setup uses SQLite and does not require PostgreSQL.

## Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `SECRET_KEY` | Django secret key | — (required in production) |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts (comma-separated) | `localhost,127.0.0.1` |
| `DB_NAME` | PostgreSQL database name | — (uses SQLite if empty) |
| `DB_USER` | PostgreSQL user | — |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_HOST` | PostgreSQL host | `db` |
| `DB_PORT` | PostgreSQL port | `5432` |

## Administration Panel

Available at `/admin/`. To create a superuser:

```bash
docker-compose exec web uv run python manage.py createsuperuser
```

## 12-Factor App

The project follows the [12-factor guidelines](https://12factor.net/):

| Factor | Implementation |
|--------|---------------|
| I. Codebase | Single Git repository on GitHub |
| II. Dependencies | Declared in `pyproject.toml` + `uv.lock` |
| III. Config | Environment variables via `.env` (never in code) |
| IV. Backing services | Configurable attachable PostgreSQL service |
| V. Build/release/run | Docker separates build and runtime |
| VI. Processes | Stateless Gunicorn, sessions in database |
| VII. Port binding | Port 8000 configurable via docker-compose |
| VIII. Concurrency | Scalable via Gunicorn workers |
| IX. Disposability | Fast startup, migrations at beginning |
| X. Dev/prod parity | Docker ensures environment parity |
| XI. Logs | Django writes logs to stdout/stderr |
| XII. Admin processes | `manage.py` for migrations and management commands |
