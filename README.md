# choosy-app

Base Django del dashboard principal de Choosy.

Ahora mismo el proyecto solo incluye la pagina principal del dashboard, planteada como esqueleto visual para seguir construyendo el resto de vistas despues.

## Ejecutar con Docker (Recomendado)

Para levantar la aplicación con PostgreSQL y uv:

```bash
sudo docker-compose up --build
```

La aplicación estará disponible en `http://localhost:8000`.

## Ejecutar con uv localmente

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Abre `http://127.0.0.1:8000/`.
