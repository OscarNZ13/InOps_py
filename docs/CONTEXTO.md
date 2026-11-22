# Contexto del proyecto

Especificación de InOps: qué problema resolverá, cómo deberá comportarse y qué reglas deberá cumplir
siempre. La propuesta de cómo aplicar los paradigmas del curso está en [PARADIGMAS.md](PARADIGMAS.md).

---

## 1. El problema

La empresa lleva el registro de sus colaboradores en un Excel maestro con unas **11,000 personas**.
Cada contratación nueva obliga a alguien a inventar a mano las **Iniciales** y la **Firma** de la
persona y a revisar que no choquen con las de nadie más.

InOps automatizará ese proceso: se capturarán los datos personales y el sistema generará Iniciales y
Firma únicas, siguiendo siempre las mismas reglas.

Varias personas podrán usar el sistema al mismo tiempo. Si dos operaciones chocan (por ejemplo, dos
personas crean a la vez colaboradores a los que les tocan las mismas Iniciales), el sistema no
mostrará un error genérico: lo resolverá o avisará en el formulario (ver sección 7.1).

---

## 2. Usuarios y roles

Los **usuarios** serán las personas que inicien sesión en InOps. No son lo mismo que los
**colaboradores**, que son las personas registradas en el sistema.

| id | Rol | Para quién |
| --- | --- | --- |
| 1 | `admin` | Administrador del sistema |
| 2 | `rrhh` | Recursos Humanos: consulta y cambio de estado |
| 3 | `dcc` | Operación completa de colaboradores |

### 2.1 Permisos por rol

| Acción | admin | dcc | rrhh |
| --- | :---: | :---: | :---: |
| Ver la lista, buscar y ver el detalle de colaboradores | ✅ | ✅ | ✅ |
| Desactivar y activar colaboradores | ✅ | ✅ | ✅ |
| Crear colaboradores | ✅ | ✅ | ❌ |
| Editar colaboradores | ✅ | ✅ | ❌ |
| Carga inicial desde Excel | ✅ | ✅ | ❌ |
| Módulo de Usuarios | ✅ | ❌ | ❌ |

### 2.2 Cómo deberán aplicarse los permisos

- **Los permisos se definirán en el código**, no en la base de datos: no habrá una matriz editable.
- **En el servidor:** cada ruta deberá declarar qué roles la pueden usar mediante un decorador, de
  forma similar a `[Authorize(Roles = "...")]` en .NET:

  ```python
  @bp.route("/create")
  @role_required("admin", "dcc")
  def create(): ...
  ```

  Si alguien sin el rol entra a esa URL, deberá recibir **403 – Acceso denegado**.
- **En las pantallas:** las tarjetas, botones y enlaces que un rol no pueda usar no deberán mostrarse.
  Ocultarlos es solo comodidad; la seguridad real la dará el decorador.
- **Sin sesión iniciada**, cualquier página interna deberá redirigir al login.

### 2.3 Registro e inicio de sesión

- **El registro será abierto:** cualquiera podrá crear su cuenta desde la página de inicio.
- **Toda cuenta nueva entrará como `rrhh`**, el rol con menos permisos. El admin le cambiará el rol a
  quien corresponda.
- **Usuario:** de 3 a 50 caracteres, único sin distinguir mayúsculas (`Ana` y `ana` son el mismo).
- **Contraseña:** mínimo 8 caracteres. Se guardará solo su hash, nunca el texto original.
- **Un usuario inactivo no podrá iniciar sesión.**

### 2.4 Módulo de Usuarios (solo admin)

| Función | Acción | Comportamiento esperado |
| --- | --- | --- |
| Listar usuarios | `list` | Mostrará todos los usuarios con su rol y su estado |
| Ver detalle | `read` | Rol, estado y fechas de creación y modificación |
| Crear usuario | `create` | Usuario, contraseña y rol elegido por el admin. Mismas reglas que el registro (sección 2.3). Entra activo |
| Editar usuario | `update` | Cambiar el nombre de usuario, el rol (`admin`, `dcc` o `rrhh`) y, opcionalmente, la contraseña |
| Activar / desactivar | `activate` / `deactivate` | Un usuario desactivado no podrá iniciar sesión y, si tenía una sesión abierta, la perderá. Nunca se borrará |

El admin **no podrá** desactivarse ni quitarse el rol de admin a sí mismo, para que el sistema nunca
se quede sin administrador. Además, siempre deberá quedar **al menos un admin activo**, aunque dos
admins se quiten el rol o se desactiven entre sí al mismo tiempo.

---

## 3. Entidades

### 3.1 Colaborador (`dbo.Collaborators`)

| Campo | Columna | Reglas |
| --- | --- | --- |
| Primer nombre | `FirstName` | Obligatorio, mínimo 2 letras |
| Segundo nombre | `SecondName` | Opcional |
| Primer apellido | `LastName` | Obligatorio, mínimo 2 letras |
| Segundo apellido | `SecondLastName` | Opcional |
| Fecha de nacimiento | `Birthdate` | Obligatoria, no puede ser futura |
| Estado | `IsActive` | Automático. Se creará siempre como *Activo* |
| Fecha de creación / modificación | `CreatedAt` / `UpdatedAt` | Automáticas |

### 3.2 Perfil del colaborador (`dbo.CollaboratorProfiles`)

Relación **1 a 1** con el colaborador.

| Campo | Columna | Reglas |
| --- | --- | --- |
| Colaborador | `id_collab` | Obligatorio, único |
| Iniciales | `Initials` | Generadas por el sistema, únicas, **nunca cambiarán** |
| Firma | `Signature` | Generada por el sistema, única, **nunca cambiará** |
| Puesto, Departamento, Teléfono | `Position`, `Department`, `Phone` | Opcionales, editables |
| Correo | `Email` | Opcional, editable, único cuando tenga valor |
| Fecha de creación / modificación | `CreatedAt` / `UpdatedAt` | Automáticas |

### 3.3 Usuario y Rol (`dbo.Users`, `dbo.Roles`)

Ver la sección 2.

---

## 4. Validación de los datos del colaborador

Antes de generar nada, el formulario deberá validar:

1. **Primer nombre y primer apellido son obligatorios** y deben tener **al menos 2 letras**.
   Si no se cumple, se mostrará el error debajo del campo y no se guardará nada:
   > El primer apellido debe tener al menos 2 letras.
2. Segundo nombre y segundo apellido son opcionales. Si se dejan vacíos o solo con espacios, se
   tratarán como si no existieran.
3. La fecha de nacimiento es obligatoria y no puede ser futura.
4. Los nombres se **guardarán** con capitalización estándar (primera letra de cada palabra en
   mayúscula, el resto en minúscula), sin importar cómo se hayan escrito: `dE lA o` → `De La O`.
5. **Dos nombres o apellidos en un solo campo.** Si el primer nombre o el primer apellido lleva un
   guion y su segundo campo está vacío (`Pérez-Soto` sin segundo apellido), probablemente son dos
   valores escritos juntos. El formulario no guardará y mostrará una advertencia:
   > Parece que escribiste dos apellidos en un campo. Escribe el segundo en «Segundo apellido».

   Junto a la advertencia habrá una casilla **"Sí, es un solo apellido"** (o "un solo nombre"). Si se
   marca, se guarda tal cual, para no impedir los apellidos compuestos que sí llevan guion.

   Es importante porque las Iniciales y la Firma nunca cambian: `Pérez-Soto` en un solo campo genera
   `OPE` / `OPerezsoto`, mientras que `Pérez` + `Soto` genera `OPS` / `OPerez`.

---

## 5. Generación de Iniciales y Firma

### 5.1 La letra extra

Tanto las Iniciales como la Firma usarán una **letra de respaldo**, que se calculará una sola vez por
colaborador con esta prioridad:

1. Si tiene **segundo apellido** → la 1.ª letra del segundo apellido.
2. Si no, si tiene **segundo nombre** → la 1.ª letra del segundo nombre.
3. Si no → la **2.ª letra del primer apellido**.

La letra irá siempre en mayúscula y siempre al **final**, sin importar de dónde salga.

> La opción 3 siempre será posible porque el primer apellido tendrá al menos 2 letras (sección 4).
> La letra extra **nunca** se tomará del primer nombre.

### 5.2 Iniciales

```
Iniciales = 1.ª letra del primer nombre + 1.ª letra del primer apellido + letra extra
```

- Las tres letras en mayúscula.
- **Si ya existen:** se agregará un número consecutivo (`1`, `2`, `3`...) hasta encontrar uno libre.

### 5.3 Firma

```
Firma base = 1.ª letra del primer nombre + primer apellido completo
```

- La inicial en mayúscula; el apellido con su primera letra en mayúscula y el resto en minúscula.
- Sin espacios: un apellido compuesto como "De la O" quedará como `Delao`.
- **Si la base ya existe:** se le agregará la letra extra.
- **Si eso también existe:** se agregará un número consecutivo (`1`, `2`, `3`...) hasta encontrar uno libre.

### 5.4 Normalización del texto

Al generar Iniciales y Firma:

1. Se quitarán los acentos (`á → a`) y la ñ (`ñ → n`).
2. Se quitarán los apóstrofos, guiones y cualquier carácter que no sea letra, dejando el texto pegado:
   `O'Neil → ONeil`, `Pérez-Soto → PerezSoto`.
3. Un nombre o apellido de varias palabras contará como **una sola unidad**: solo se tomará la letra
   de la primera palabra, nunca una por palabra.
4. En la Firma se eliminarán los espacios internos del primer apellido.

### 5.5 Casos de ejemplo

Cada flecha es el resultado esperado cuando el valor anterior ya está ocupado.

| Colaborador | Origen de la letra extra | Iniciales | Firma |
| --- | --- | --- | --- |
| Oscar Josue Naranjo Zuniga | 2.º apellido (Z) | ONZ → ONZ1 → ONZ2 | ONaranjo → ONaranjoZ → ONaranjoZ1 → ONaranjoZ2 |
| Oscar Naranjo Zuniga | 2.º apellido (Z) | ONZ → ONZ1 → ONZ2 | ONaranjo → ONaranjoZ → ONaranjoZ1 → ONaranjoZ2 |
| Oscar Josue Naranjo | 2.º nombre (J) | ONJ → ONJ1 → ONJ2 | ONaranjo → ONaranjoJ → ONaranjoJ1 → ONaranjoJ2 |
| Oscar Naranjo | 2.ª letra del 1.er apellido (A) | ONA → ONA1 → ONA2 | ONaranjo → ONaranjoA → ONaranjoA1 → ONaranjoA2 |
| Oscar De la O Lopez | 2.º apellido (L) | ODL → ODL1 → ODL2 | ODelao → ODelaoL → ODelaoL1 → ODelaoL2 |
| Ángel Muñoz | 2.ª letra del 1.er apellido (U) | AMU | AMunoz |
| Oscar O | — | ❌ Error de validación: el primer apellido debe tener al menos 2 letras | ❌ |

### 5.6 Inmutabilidad

- Las Iniciales y la Firma se generarán **una sola vez**, al crear al colaborador.
- Editar después su nombre o apellido **no** las recalculará.
- El sistema deberá **impedir** cualquier intento de modificarlas, aunque venga de código nuevo.

---

## 6. Flujo de creación de un colaborador

1. Se capturarán los datos personales y, opcionalmente, puesto, departamento, correo y teléfono.
2. Se validarán según la sección 4.
3. Se normalizará la capitalización de los nombres.
4. Se guardará el colaborador. Si falla, el proceso se detendrá y se informará el error.
5. Se calculará la letra extra y se generarán Iniciales y Firma, comparando contra **todos** los
   perfiles existentes: activos, inactivos y migrados del Excel.
6. Se guardará el perfil ligado al colaborador. Si falla, el colaborador del paso 4 se revertirá.
7. Se mostrará una confirmación con las Iniciales y la Firma generadas.

Los pasos 4 a 6 deberán ocurrir en **una sola transacción**: o se guardan colaborador y perfil, o ninguno.

---

## 7. Reglas de integridad

El sistema deberá garantizar siempre que:

- Nunca haya dos colaboradores con las mismas Iniciales.
- Nunca haya dos colaboradores con la misma Firma.
- Nunca exista un colaborador sin su perfil: o existen ambos o ninguno.
- La unicidad se valide contra todos los colaboradores, incluidos los inactivos y los migrados.
- Los colaboradores y los usuarios **nunca se eliminen**: solo se desactiven.
- Las Iniciales y la Firma nunca cambien después de creadas.

### 7.1 Operaciones simultáneas

La base de datos es la que garantiza la unicidad (restricciones `UNIQUE`): aunque dos personas
guarden en el mismo instante, nunca quedarán dos registros con el mismo valor. Lo que el sistema
deberá cuidar es qué ve la persona cuyo guardado rechaza la base:

| Choque | Comportamiento esperado |
| --- | --- |
| Dos colaboradores nuevos generan las mismas Iniciales o Firma | Se generan de nuevo (el siguiente valor libre) y se guarda sin que la persona lo note |
| Dos personas guardan el mismo nombre de usuario | Se muestra "Ese usuario ya existe." en el formulario, sin perder lo escrito |
| Dos perfiles guardan el mismo correo | Se muestra el error en el campo de correo |
| Dos admins se quitan el rol o se desactivan entre sí | El segundo espera a que termine el primero y recibe "Debe quedar al menos un administrador activo." |

---

## 8. Módulos

Al iniciar sesión, la página de inicio mostrará una tarjeta por módulo. Cada rol verá solo las
tarjetas que pueda usar.

| Módulo | Roles |
| --- | --- |
| Lista de colaboradores | admin, dcc, rrhh |
| Nuevo colaborador | admin, dcc |
| Carga inicial | admin, dcc |
| Usuarios | admin |

### 8.1 Lista de colaboradores

| Función | Comportamiento esperado |
| --- | --- |
| Listar | Mostrará los colaboradores con su nombre completo, Iniciales, Firma y estado. Deberá estar paginada, porque son miles de registros |
| Filtrar por estado | **Activos** (por defecto), **Inactivos** o **Todos** |
| Buscar | Un selector elegirá el campo: **Nombre**, **Iniciales** o **Firma**. La búsqueda será parcial ("contiene") y no distinguirá mayúsculas ni acentos. Por Nombre buscará en nombres y apellidos |
| Ver detalle | Todos los datos del colaborador y de su perfil |
| Editar | Solo admin y dcc. Datos personales y campos editables del perfil; nunca Iniciales ni Firma |
| Desactivar / activar | Todos los roles. Cambiará el estado; nunca borrará el registro |

### 8.2 Nuevo colaborador

Formulario con los campos de la sección 3, la validación de la sección 4 y el flujo de la sección 6.
Al terminar, mostrará las Iniciales y la Firma generadas.

### 8.3 Carga inicial

El sistema deberá empezar con los **~11,000 registros del Excel maestro**, respetando sus Iniciales y
Firmas actuales, antes de dar de alta colaboradores nuevos. Su diseño se definirá en una etapa
posterior, cuando se conozca el formato exacto del Excel; mientras tanto, su tarjeta se mostrará como
"Próximamente".

### 8.4 Usuarios

Ver la sección 2.4.
