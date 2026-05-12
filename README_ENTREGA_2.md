# 🚀 Implementación de Funcionalidades Web 2.0

Se han incorporado mecanismos para que los usuarios registrados puedan interactuar dinámicamente con la aplicación sin depender de la administración de Django.

## 🛠 Cambios realizados:

*   **Modelos habilitados:** Se permite la creación de **Grupos**, **Propuestas de Plan** (PlanProposal) y **Opciones de Plan** (Plan) por parte de los usuarios.
*   **Vistas (Views):** Se implementaron clases basadas en `CreateView` en `core/web/crud.py` para gestionar el procesamiento de datos de forma limpia y reutilizable.
*   **Formularios (Forms):** Se crearon clases en `core/forms.py` basadas en `ModelForm`, integrando las clases de CSS del proyecto (`groups-input`, `groups-textarea`) para mantener la estética premium.
*   **Seguridad:** Se aplicó restricción de acceso mediante `LoginRequiredMixin`. Solo usuarios con sesión activa pueden visualizar y enviar los formularios de creación.
*   **Automatización de Datos:** Se configuró el método `form_valid` para asignar automáticamente el usuario actual como propietario (`owner`) o creador (`created_by`) de las nuevas instancias. En el caso de los Grupos, el creador se añade automáticamente como miembro con rol de Propietario.

## 📂 Archivos modificados/creados:

*   `core/forms.py`: Definición de `GroupForm`, `PlanProposalForm` y `PlanForm`.
*   `core/web/crud.py`: Lógica de creación mediante `GroupCreateView`, `PlanProposalCreateView` y `PlanCreateView`.
*   `core/views.py`: Exportación de las nuevas vistas.
*   `core/urls.py`: Nuevas rutas asignadas (`/crear-grupo/`, `/crear-propuesta/`, `/crear-plan/`).
*   `front/templates/pages/crear_entidad.html`: Interfaz de usuario premium y dinámica para la carga de datos.

## 📝 Cómo probarlo:

1.  Inicia sesión con una cuenta de usuario normal.
2.  Navega a la URL `/crear-grupo/` para fundar un nuevo equipo.
3.  Navega a `/crear-propuesta/` para sugerir una nueva actividad a un grupo.
4.  Navega a `/crear-plan/` para añadir opciones específicas a una propuesta.
5.  Completa los formularios y presiona "Guardar Entidad".
6.  Verifica que las nuevas instancias aparecen en tus grupos o en el dashboard principal.
