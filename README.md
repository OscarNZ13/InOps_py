# InOps

Sistema web para registrar a los colaboradores de la empresa y generar automáticamente sus
**Iniciales** y su **Firma**, garantizando que nunca se repitan entre las ~11,000 personas registradas.

**Stack:** Python · Flask · SQLAlchemy · Flask-Login · Flask-WTF · SQL Server · pytest

## Documentación

| Documento | Para qué sirve |
| --- | --- |
| [docs/INSTALACION.md](docs/INSTALACION.md) | Instalar, configurar y correr el proyecto desde cero en Windows |
| [docs/CONTEXTO.md](docs/CONTEXTO.md) | Especificación: el problema, roles y permisos, reglas de negocio y módulos |
| [docs/PARADIGMAS.md](docs/PARADIGMAS.md) | Los 4 paradigmas del curso: dónde podría implementarse cada uno y por qué |

## Inicio rápido

Para quien ya tiene SQL Server con las bases creadas (si no, seguir la [guía de instalación](docs/INSTALACION.md)):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask run
```

## Estructura

```
app/
  __init__.py          Fábrica de la aplicación (create_app)
  config.py            Configuración por entorno, leída desde .env
  extensions.py        Instancias compartidas: base de datos, CSRF y login
  core/                Código común: tipos de modelos, permisos por rol y tarjetas del inicio
  modules/             Un paquete por módulo funcional (Blueprint)
    auth/              Login, registro y logout de los usuarios del sistema
    colaboradores/     Lista, búsqueda y alta de colaboradores
  templates/           Plantillas HTML (Jinja2), una carpeta por módulo
  static/              CSS y archivos estáticos
database/              Scripts SQL que crean las bases de datos
docs/                  Documentación del proyecto
tests/                 Pruebas automáticas (pytest)
run.py                 Punto de entrada de la aplicación
```
