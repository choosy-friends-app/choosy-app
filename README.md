# choosy-app

Choosy es una app mobile-first para proponer planes con amigos, votar juntos y decidir rapido.

## Migracion a Django

La version visual de v0 se migro a Django manteniendo las 4 pantallas principales:
- Home: `/`
- Groups: `/groups/`
- Discover: `/discover/`
- Profile: `/profile/`

La carpeta original de v0 (`/social-plan-app`) se conserva como referencia.

## Ejecutar el proyecto

1. Crear y activar entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Aplicar migraciones:

```bash
python manage.py migrate
```

4. Ejecutar servidor:

```bash
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`.
