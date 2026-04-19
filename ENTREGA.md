# Deliverable 1 — Choosy App

**Course:** 2025/26  
**Subject:** Web Project  
**Group:** choosy-friends-app

---

## 1. GitHub public address

**https://github.com/choosy-friends-app/choosy-app**

The code is available in this GitHub repository created specifically for this purpose. The repository is publicly accessible without any authentication. Each participant member of the team has contributed using a different GitHub username, as requested.

---

## 2. Design decisions

### Proposed scenario
The Choosy application solves the problem of collective decision-making in groups (leisure plans, restaurants, activities). The model reflects a complete workflow: a group of people proposes options, votes on them, and the final decision is saved as history.

### Data model
Six entities have been implemented with complex relationships:

- **Group** — Central entity with state (planning/voting/active/archived), hero image, interests (JSON field), and mission.
- **GroupMember** — M2M relationship between User and Group, enriched with role (owner/admin/member) and invitation status (invited/active/left). Allows members without a registered account (display_name + avatar_url).
- **PlanProposal** — Temporal voting round. Restricted to only one open proposal per group (conditional unique constraint).
- **Plan** — Individual option within a proposal. Includes price, duration, tag, location, and image. Explicit ordering (option_order).
- **Vote** — Upvote/downvote system. Supports three modes of identification: authenticated member, session user, or anonymous session. Unique constraints at the database level to prevent double voting.
- **Notification** — Internal notification system for invitations, new plans, and decisions. Linked to the group and proposal for context.

All entities inherit from `TimestampedModel` (abstract) to automatically include `created_at` and `updated_at`.

### Application architecture
- Views are organized by functionality inside `core/web/` (auth, dashboard, groups, plans, notifications, shared) instead of a single `views.py` file, to improve maintainability.
- Shared utilities (decorators, query helpers, template enrichment) are centralized in `shared.py`.
- The frontend uses Django Template Language with reusable components in `front/templates/includes/`, avoiding external JS frameworks.
- CSS is modular per page/functionality to prevent collisions and ease maintenance.

### Authentication
It uses the built-in Django authentication system (`django.contrib.auth`) with a custom registration form (`RegisterForm`) that includes email validation.

### Docker and deployment
- The configuration automatically switches between SQLite (local development) and PostgreSQL (Docker) depending on whether the `DB_NAME` environment variable is defined.
- Gunicorn is used as the production WSGI server (instead of the Django development server).
- Database migrations are automatically executed when the container starts.

### 12-Factor App
The project implements the 12-factor app guidelines: configuration via environment variables, dependencies declared in `pyproject.toml` + `uv.lock`, logs to stdout, stateless processes, and dev/prod parity via Docker. See the README file for full details.

---

## 3. Grade distribution

All members of the group have worked and contributed equally to the project. Therefore, the grades should be perfectly equal for all members of the team.

---

## 4. Instructions on how to run/deploy the application

To run and deploy the application using Docker, follow these steps:

1. Clone the repository and navigate to the project root:
   ```bash
   git clone https://github.com/choosy-friends-app/choosy-app.git
   cd choosy-app
   ```

2. Copy the example environment variables file to create your local configuration:
   ```bash
   cp .env.example .env
   ```

3. Build and start the Docker containers:
   ```bash
   docker-compose up --build
   ```

4. The application will automatically execute the necessary database migrations during the container startup.

5. Open your web browser and access the application at:
   **http://localhost:8000**

For more detailed deployment instructions and development setup, please refer to the `README.md` file located at the root of the project.
