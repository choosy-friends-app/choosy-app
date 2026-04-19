# Choosy App

Aplicación web colaborativa para tomar decisiones en grupo. Permite a grupos de usuarios proponer planes, votar entre opciones y recibir notificaciones en tiempo real. Desarrollada con Django como proyecto de la asignatura **Projecte Web** (Grau en Enginyeria Informàtica, UdL 2025/26).

## Funcionalidades

- Autenticación y registro de usuarios
- Gestión de grupos con roles (Owner, Admin, Member)
- Sistema de invitaciones con aceptación/rechazo
- Propuestas de planes con votación por opción (upvote/downvote)
- Centro de notificaciones con contador en tiempo real
- Historial y archivo de planes anteriores
- Panel de administración Django

## Stack tecnológico

- **Backend**: Django 5.1+ (Python 3.12)
- **Base de datos**: PostgreSQL 16 (Docker) / SQLite3 (desarrollo local)
- **Servidor**: Gunicorn (producción)
- **Gestor de dependencias**: uv
- **Contenedores**: Docker + docker-compose

## Modelo de datos

El modelo incluye 6 entidades con relaciones complejas:

- `Group` — Grupo de usuarios con estado y metadatos
- `GroupMember` — Relación usuario-grupo con rol y estado de invitación
- `PlanProposal` — Ronda de votación con ventana temporal
- `Plan` — Opción individual dentro de una propuesta
- `Vote` — Voto de un miembro a un plan
- `Notification` — Notificaciones de invitaciones, nuevos planes y decisiones

## Ejecutar con Docker (Recomendado)

### 1. Clonar el repositorio

```bash
git clone https://github.com/choosy-friends-app/choosy-app.git
cd choosy-app
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y establece un `SECRET_KEY` seguro para producción. Para desarrollo local puedes usar los valores por defecto.

### 3. Levantar la aplicación

```bash
docker-compose up --build
```

La aplicación estará disponible en `http://localhost:8000`.

El comando ejecuta automáticamente las migraciones al arrancar.

### 4. (Opcional) Crear datos de demo

```bash
docker-compose exec web uv run python manage.py seed_demo_users
```

Crea los usuarios: `aleix`, `bru`, `eldejuneda`, `chileno` (contraseña: `demo1234` para todos).

## Ejecutar localmente con uv

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. En local usa SQLite, no requiere PostgreSQL.

## Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `SECRET_KEY` | Clave secreta de Django | — (obligatorio en producción) |
| `DEBUG` | Modo debug | `False` |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por coma) | `localhost,127.0.0.1` |
| `DB_NAME` | Nombre de la base de datos PostgreSQL | — (sin esto usa SQLite) |
| `DB_USER` | Usuario de PostgreSQL | — |
| `DB_PASSWORD` | Contraseña de PostgreSQL | — |
| `DB_HOST` | Host de PostgreSQL | `db` |
| `DB_PORT` | Puerto de PostgreSQL | `5432` |

## Panel de administración

Disponible en `/admin/`. Para crear un superusuario:

```bash
docker-compose exec web uv run python manage.py createsuperuser
```

## 12-Factor App

El proyecto sigue las [12-factor guidelines](https://12factor.net/):

| Factor | Implementación |
|--------|---------------|
| I. Codebase | Repositorio Git único en GitHub |
| II. Dependencies | Declaradas en `pyproject.toml` + `uv.lock` |
| III. Config | Variables de entorno via `.env` (nunca en código) |
| IV. Backing services | PostgreSQL como servicio adjunto configurable |
| V. Build/release/run | Docker separa build y runtime |
| VI. Processes | Gunicorn sin estado, sesiones en base de datos |
| VII. Port binding | Puerto 8000 configurable vía docker-compose |
| VIII. Concurrency | Escalable vía workers de Gunicorn |
| IX. Disposability | Arranque rápido, migraciones al inicio |
| X. Dev/prod parity | Docker garantiza paridad de entornos |
| XI. Logs | Django escribe logs a stdout/stderr |
| XII. Admin processes | `manage.py` para migraciones y comandos de gestión |
