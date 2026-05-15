# Deliverable 2 (Web 2.0) - Choosy

## 1) GitHub Repository

- Public repository URL: https://github.com/choosy-friends-app/choosy-app
- Working branch for this delivery: `second_activity`
- `db.sqlite3` is committed at repository root to simplify evaluation.
- Repository access should be granted to the requested evaluator user (`rogargon`).

## 2) Users for Evaluation

### Admin user

- Username: `admin`
- Password: `admin1234`

### Relevant functional users

- `aleix` / `demo1234`
- `bru` / `demo1234`
- `eldejuneda` / `demo1234`
- `chileno` / `demo1234`

### Automatic user provisioning

- On container startup (`docker-compose up` / `podman-compose up`), the `web` service runs:
  1. `python manage.py migrate`
  2. `python manage.py seed_demo_users`
  3. `gunicorn ...`
- This guarantees demo users are available in fresh environments.

## 3) Design Decisions and Main Changes vs Deliverable 1

### Web 2.0 CRUD implementation (without Django admin)

- Implemented create/update/delete flows for user-manageable entities:
  - `Group`
  - `PlanProposal`
  - `Plan`
- Implemented with Django Class-Based Views + ModelForms:
  - `CreateView`, `UpdateView`, `DeleteView`
  - `GroupForm`, `PlanProposalForm`, `PlanForm`

### Authorization and integrity rules

- Ownership restrictions for edit/delete (`OwnerRequiredMixin`).
- Proposal ownership filtering in forms to prevent cross-user modifications.
- Closed proposal protection: options cannot be modified/added once proposal is closed.
- Added graceful handling for option-order conflicts during plan creation.

### External API integration (AJAX + jQuery/fetch)

- Added backend proxy endpoints:
  - `GET /api/locations/search/` (OpenStreetMap Nominatim)
  - `GET /api/weather/forecast/` (Open-Meteo)
- Integrated in create/edit plan UX:
  - Live location autocomplete
  - Forecast preview for selected coordinates/date
- Includes validation and resilient error handling (unavailable API, invalid params, out-of-range forecast date).

### UI/branding cleanup

- Replaced placeholder/AI-style branding text with Choosy branding.
- Added Choosy logo assets and favicon integration in base/auth layouts.

## 4) E2E and Test Coverage (Required by Deliverable 2)

### End-to-end tests (Behave + Splinter)

- Feature file: `features/crud.feature`
- Steps: `features/steps/crud_steps.py`
- Coverage includes:
  - Create, update, delete for `Group`, `PlanProposal`, `Plan`
  - Validation errors (required fields / invalid data)
  - Security restrictions (unauthorized user cannot edit/delete other users' entities)

Latest run:

- `behave`: **13 scenarios passed**, **108 steps passed**

### Django unit/integration/security tests

- `python manage.py test`: **13 tests passed**
- Includes security and integration checks for CRUD restrictions and API behavior.

## 5) Evaluation Mapping (Deliverable 2 Rubric)

- **Create instances (3 points):** Implemented for Group/Proposal/Plan + E2E coverage.
- **Modify instances (3 points):** Implemented for Group/Proposal/Plan + E2E coverage + ownership restrictions.
- **Remove instances (1.5 points):** Implemented for Group/Proposal/Plan + E2E coverage + ownership restrictions.
- **Use API (2.5 points):** Functional, non-trivial integration with 2 external APIs and AJAX-assisted forms.

## 6) Notes for Evaluator

- Main app flows can be validated from UI (no Django admin required).
- If needed, demo data can be re-generated with:
  - `python manage.py seed_demo_users`
