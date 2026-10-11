# Guía de instalación

Pasos para dejar InOps funcionando en una computadora con **Windows** después de clonar el repositorio.

> Cada instalación usa **su propio SQL Server local**: las bases de datos no se comparten.
> El repositorio solo contiene el código y los scripts que crean las bases.

---

## 1. Programas necesarios

| Programa | Para qué | Notas |
| --- | --- | --- |
| **Git** | Clonar el repositorio | |
| **Python 3.10 a 3.14** | Ejecutar el proyecto | Al instalar, marcar *"Add Python to PATH"*. Python 3.15 todavía no es compatible con `pyodbc` |
| **SQL Server** (Express o Developer) | Base de datos | Ambas ediciones son gratuitas |
| **SSMS** (SQL Server Management Studio) | Ejecutar los scripts SQL | |
| **ODBC Driver 17 o 18 for SQL Server** | Conectar Python con SQL Server | Se descarga aparte de SQL Server |
| **SWI-Prolog 10** (opcional) | Motor de reglas en Prolog | Solo para usar o probar el motor Prolog; sin él, el sistema usa el motor Python. Se instala con `winget install SWI-Prolog.SWI-Prolog`. Python lo encuentra solo; para usar `swipl` en la terminal, agregar `C:\Program Files\swipl\bin` al PATH |
| **PyCharm** (opcional) | Editor recomendado | Ver la sección 8 |

Para saber qué driver ODBC tienes instalado, en PowerShell:

```powershell
Get-OdbcDriver | Select-Object Name
```

Debe aparecer `ODBC Driver 17 for SQL Server` o `ODBC Driver 18 for SQL Server`.

---

## 2. Clonar el repositorio

```powershell
git clone <url-del-repositorio> InOps
cd InOps
```

---

## 3. Crear las bases de datos

En **SSMS**, conectarse al servidor local y ejecutar, en este orden:

1. `database/01_crear_bd.sql`: crea la base `InOps` con sus tablas y los roles iniciales.
2. `database/00_crear_bd_pruebas.sql`: crea la base vacía `InOps_Test`, que usan las pruebas.

Para ejecutar un script: *File → Open → File*, elegir el `.sql` y presionar **Execute** (F5).

Anota el **nombre del servidor** que aparece en la ventana de conexión de SSMS
(por ejemplo `MI-PC`, `localhost` o `localhost\SQLEXPRESS`). Se usa en el paso 6.

---

## 4. Crear el entorno virtual

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Al activarse, la línea de la terminal empieza con `(.venv)`.

Si tienes varias versiones de Python instaladas, elige la versión al crear el entorno:

```powershell
py -3.14 -m venv .venv
```

Si aparece el error *"running scripts is disabled on this system"*, ejecuta esto una sola vez y vuelve a activar:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

> **Cada vez que abras una terminal nueva**, activa el entorno con `.venv\Scripts\activate`.

---

## 5. Instalar las librerías

Con `(.venv)` activo:

```powershell
pip install -r requirements.txt
```

Debe terminar con `Successfully installed ...`.

---

## 6. Configurar el archivo `.env`

El `.env` guarda la configuración **personal** de cada computadora: la clave secreta y la conexión a la base.
**Nunca se sube a git.**

**6.1** Crearlo a partir de la plantilla:

```powershell
copy .env.example .env
```

**6.2** Generar una clave secreta propia:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**6.3** Abrir `.env` y completar los valores marcados con `< >`:

```ini
SECRET_KEY=<la clave generada en el paso 6.2>

FLASK_ENV_NAME=development
FLASK_APP=run.py

DATABASE_URL=mssql+pyodbc://@<SERVIDOR>/InOps?driver=ODBC+Driver+<17 o 18>+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
TEST_DATABASE_URL=mssql+pyodbc://@<SERVIDOR>/InOps_Test?driver=ODBC+Driver+<17 o 18>+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
```

| Tu instalación de SQL Server | Valor de `<SERVIDOR>` |
| --- | --- |
| Instancia por defecto | `localhost` o el nombre de tu PC |
| SQL Server Express | `localhost\SQLEXPRESS` |

> `trusted_connection=yes` entra a SQL Server con tu usuario de Windows, sin contraseña.
>
> Si `TEST_DATABASE_URL` se borra, las pruebas usan una base SQLite en memoria.

---

## 7. Verificar que todo funciona

**7.1 Conexión a la base de datos:**

```powershell
python -c "from sqlalchemy import text; from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); print(db.session.execute(text('SELECT DB_NAME(), @@SERVERNAME')).one()); print([r[0] for r in db.session.execute(text('SELECT name FROM sys.tables ORDER BY name'))])"
```

Resultado esperado (con el nombre de tu servidor):

```
('InOps', 'TU-SERVIDOR')
['CollaboratorProfiles', 'Collaborators', 'Roles', 'Users']
```

**7.2 La aplicación:**

```powershell
flask run
```

Abre `http://127.0.0.1:5000`: debe mostrarse la página de inicio de InOps. `Ctrl + C` la detiene.

**7.3 Las pruebas:**

```powershell
pytest
```

Todas las pruebas deben pasar.

---

## 8. Configurar PyCharm (opcional)

1. **File → Open** y elegir la carpeta del proyecto.
2. **Settings → Project: InOps → Python Interpreter → Add Interpreter → Add Local Interpreter**,
   elegir **Virtualenv → Existing** y seleccionar `.venv\Scripts\python.exe`.
3. **Run → Edit Configurations → + → Flask server**:
   - **Target type:** Script path
   - **Target:** `run.py` del proyecto
4. Clic derecho sobre `app/templates` → **Mark Directory as → Template Folder**.

Con eso, el botón ▶ arranca la aplicación.

---

## 9. Problemas comunes

| Error | Causa | Solución |
| --- | --- | --- |
| `running scripts is disabled on this system` | Política de seguridad de PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `Failed to build installable wheels ... pyodbc` | Versión de Python no compatible | Recrear `.venv` con Python 3.14 o anterior (paso 4) |
| `Falta SECRET_KEY` o `Falta DATABASE_URL` | No existe `.env`, está vacío o se guardó como `.env.txt` | Revisar el paso 6 |
| `Data source name not found and no default driver specified` | El driver del `.env` no coincide con el instalado | Revisar `Get-OdbcDriver` y ajustar `17` / `18` |
| `Cannot open database "InOps"` | La base no existe | Ejecutar los scripts del paso 3 |
| `Login failed for user` | Tu usuario de Windows no tiene acceso a SQL Server | Revisar los permisos desde SSMS |
| `No module named 'flask'` | El entorno virtual no está activo | `.venv\Scripts\activate` |
