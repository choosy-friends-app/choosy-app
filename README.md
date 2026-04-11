# choosy-app

Base Django del dashboard principal de Choosy.

Ahora mismo el proyecto solo incluye la pagina principal del dashboard, planteada como esqueleto visual para seguir construyendo el resto de vistas despues.

## Ejecutar con uv

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Abre `http://127.0.0.1:8000/`.
