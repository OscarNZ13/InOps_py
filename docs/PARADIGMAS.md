# Paradigmas de programación

InOps será el proyecto final del curso **SC-250 Paradigmas de Programación** y deberá aplicar cuatro
paradigmas. Este documento propone **dónde podría implementarse cada uno y por qué es la herramienta
adecuada para ese problema**. La regla es que ningún paradigma esté de adorno: cada uno deberá
resolver un requisito real de [CONTEXTO.md](CONTEXTO.md).

| Paradigma | Problema que resolvería | Dónde podría implementarse |
| --- | --- | --- |
| **Orientado a objetos** | Modelar las entidades y tener motores de reglas intercambiables | Modelos (`*/models.py`, `core/models_base.py`) y la interfaz del motor (`rules/engine.py`) |
| **Funcional** | Generar Iniciales y Firma de forma predecible y comprobable | Motor en Python (`rules/python_engine.py`) |
| **Lógico** | Expresar las reglas de negocio como hechos y reglas | Motor en Prolog (`rules/rules.pl` y `rules/prolog_engine.py`) |
| **Orientado a eventos** | Reaccionar a las acciones del usuario y garantizar que Iniciales y Firma nunca cambien | Rutas (`*/routes.py`) y eventos del ORM (`collaborators/events.py`) |

`rules/` se refiere a `app/modules/collaborators/rules/`. Las rutas de archivo son una sugerencia;
lo importante es dónde vive cada responsabilidad.

---

## La pieza central: un motor de reglas con dos implementaciones

La propuesta es que la generación de Iniciales y Firma viva en un **motor de reglas** con dos
implementaciones que hagan exactamente lo mismo:

```
                        RulesEngine  (clase abstracta)
                     ┌───────┴────────┐
              PythonEngine         PrologEngine
              (funcional)          (lógico, con rules.pl)
```

Así, un solo componente demuestra tres paradigmas: objetos, funcional y lógico.

- **Las dos implementaciones cumplirían la misma interfaz:** `extra_letter`, `generate_initials` y
  `generate_signature`.
- **El motor se elegiría en el `.env`** con `RULES_ENGINE=python` o `RULES_ENGINE=prolog`. El servicio
  que crea colaboradores no debería saber cuál recibió.
- **Las mismas pruebas** deberían correr contra los dos motores, con los casos de la sección 5.5 de
  [CONTEXTO.md](CONTEXTO.md), y ambos tendrían que dar resultados idénticos.
- **El motor por defecto sería `python`.** El motor Prolog necesita **SWI-Prolog** instalado; si no
  está, sus pruebas deberían saltarse solas y el sistema seguir funcionando con Python.

Interfaz sugerida:

```python
Exists = Callable[[str], bool]


class RulesEngine(ABC):
    @abstractmethod
    def extra_letter(self, second_last_name: str | None, second_name: str | None,
                     last_name: str) -> str: ...

    @abstractmethod
    def generate_initials(self, first_name: str, last_name: str, extra: str,
                          exists: Exists) -> str: ...

    @abstractmethod
    def generate_signature(self, first_name: str, last_name: str, extra: str,
                           exists: Exists) -> str: ...
```

`exists` sería una función que responde si un valor ya está ocupado: en las pruebas, un `set`; en la
aplicación, una consulta a la base de datos.

---

## 1. Orientado a objetos

**Idea:** el programa se organiza en objetos que combinan datos y comportamiento.

| Concepto | Dónde podría aplicarse |
| --- | --- |
| **Clases y objetos** | Un modelo por tabla: `User`, `Role`, `Collaborator`, `CollaboratorProfile`. Cada fila de la base sería un objeto |
| **Encapsulamiento** | Métodos como `User.set_password()` y `check_password()`, para que nadie manipule el hash de la contraseña directamente |
| **Herencia** | Los modelos heredando de `db.Model` y, en el caso de `User`, de `UserMixin` de Flask-Login |
| **Mixins** | Un `TimestampMixin` que agregue `CreatedAt` y `UpdatedAt` a cualquier modelo sin repetir código |
| **Abstracción** | `RulesEngine` definiendo *qué* hace un motor de reglas, no *cómo* |
| **Polimorfismo** | `PythonEngine` y `PrologEngine` usándose igual: el servicio llamaría `engine.generate_signature(...)` sin saber cuál es |

**Por qué aquí:** el polimorfismo permitiría que Prolog sea opcional sin romper nada. Si en una
máquina no se puede instalar SWI-Prolog, bastaría con `RULES_ENGINE=python` y el resto del sistema no
cambiaría.

---

## 2. Funcional

**Idea:** construir el programa componiendo **funciones puras**: el mismo input siempre da el mismo
output y la función no modifica nada fuera de ella.

| Concepto | Dónde podría aplicarse |
| --- | --- |
| **Funciones puras** | `normalize`, `first_letter`, `extra_letter`, `generate_initials` y `generate_signature`, sin leer ni escribir estado global |
| **Funciones de orden superior** | Los generadores recibiendo `exists` como parámetro |
| **Composición** | `first_letter` como normalizar → tomar la primera palabra → tomar la primera letra → mayúscula |
| **Evaluación perezosa** | Un generador infinito `candidates("ONZ")` que produzca `ONZ`, `ONZ1`, `ONZ2`... y solo calcule lo que se pida |
| **Expresiones en lugar de instrucciones** | Comprensiones y generadores en lugar de ciclos con variables que cambian |

Ejemplo de referencia:

```python
def candidates(base):
    yield base
    yield from (f"{base}{n}" for n in itertools.count(1))


def first_available(options, exists):
    return next(o for o in options if not exists(o))
```

**Por qué aquí:** las reglas de Iniciales y Firma son funciones matemáticas: dado un nombre y los
valores ocupados, el resultado está determinado. Al ser puras, podrían probarse sin base de datos,
reutilizarse igual desde el alta y desde la carga del Excel, y no tendrían efectos ocultos que
pudieran generar un duplicado.

---

## 3. Lógico (Prolog)

**Idea:** en lugar de decir *cómo* calcular algo, se declaran **hechos** y **reglas**, y se hacen
**preguntas**. Prolog encuentra la respuesta por **unificación** y **backtracking**.

| Concepto | Dónde podría aplicarse |
| --- | --- |
| **Cláusulas de Horn** | Cada regla de `rules.pl` con la forma *conclusión :- condiciones* |
| **Orden de cláusulas y corte (`!`)** | La jerarquía de la letra extra como tres cláusulas en orden; el corte evitaría probar las siguientes |
| **Backtracking** | Un predicado `available/2` que pruebe `N = 1, 2, 3...` hasta encontrar un valor libre |
| **Negación por falla** | `\+ used(X)`: "X no está usada" significa "no se puede demostrar que lo esté" |
| **Unificación** | Las variables de salida llenándose al encontrar una solución |
| **Predicados foráneos** | Un `used/1` escrito en Python, para que Prolog le pregunte a la base de datos |

Ejemplo de referencia:

```prolog
extra_letter(SA, _, _, L) :- SA \== '', !, first_letter(SA, L).
extra_letter(_, SN, _, L) :- SN \== '', !, first_letter(SN, L).
extra_letter(_, _, PA, L) :- without_spaces(PA, S), sub_atom(S, 1, 1, _, X), upcase_atom(X, L).

available(Base, Base) :- \+ used(Base), !.
available(Base, C)    :- between(1, inf, N), atom_concat(Base, N, C), \+ used(C), !.
```

**Por qué aquí:** el documento de contexto ya está escrito como reglas lógicas; la letra extra se lee
casi igual en español que en Prolog.

**Responsabilidades entre lenguajes:** Python validaría y normalizaría el texto (acentos, ñ, espacios)
y consultaría la base; Prolog decidiría.

---

## 4. Orientado a eventos

**Idea:** el programa no sigue un flujo fijo; **reacciona** a eventos mediante manejadores registrados.

| Concepto | Dónde podría aplicarse |
| --- | --- |
| **Manejadores de peticiones HTTP** | Cada función con `@bp.route(...)`, que se ejecuta cuando llega esa petición |
| **Hooks del ciclo de vida** | `@bp.before_request` para exigir sesión en todo un módulo, y el decorador de roles de cada ruta |
| **Callbacks** | `@login_manager.user_loader`, que Flask-Login invoca en cada petición para recuperar al usuario |
| **Eventos de conexión** | `@event.listens_for(Engine, "connect")` para configurar la base al conectarse |
| **Eventos del ORM** | Un `before_update` sobre `CollaboratorProfile` que impida cambiar Iniciales o Firma |
| **Señales (opcional)** | `user_logged_in` / `user_logged_out` para una bitácora de accesos |

Ejemplo de referencia:

```python
@event.listens_for(CollaboratorProfile, "before_update")
def prevent_identifier_changes(mapper, connection, profile):
    state = inspect(profile)
    for field in ("initials", "signature"):
        if state.attrs[field].history.has_changes():
            raise ImmutableProfileError(f"No se puede modificar '{field}' de un perfil existente.")
```

**Por qué aquí:** el contexto exige que Iniciales y Firma **nunca** cambien. Sin un evento, esa regla
dependería de que ningún programador lo olvide; con el evento, sería el sistema quien la garantice.
