# Arquitectura y mapa del código fuente

Esta página orienta a quienes mantienen el runtime, SDK, mapas y skins. No es necesario modificar estos archivos para crear un mod normal.

## Proyecto

- Motor: Unity `6000.3.8f1`.
- Gameplay: 2D con URP 2D e Input System.
- Código de juego: `Assembly-CSharp`.
- Modding oficial: datos externos validados, sin C# externo.

## Runtime `.jfmod`

Directorio principal:

```text
Assets/Jumpfall/Modding/
```

Responsabilidades del conjunto:

- bootstrap antes de la primera escena;
- descubrimiento de carpetas y `.jfmod`;
- extracción segura y caché;
- lectura y validación de `jumpfall.mod.json`;
- resolución de dependencias, conflictos y prioridad;
- perfil activo/pendiente;
- gestor F10;
- aplicación de parches, localización, menús y player tuning;
- staging de mapas `.jfue`.

`ModContentRuntime` aplica contenido validado y nunca carga ensamblados del paquete. Busca nuevos `PlayerMovement` periódicamente para aplicar tuning a jugadores creados al cambiar de escena.

### PlayerMovement y estados runtime

El componente público sigue siendo `PlayerMovement`, pero su implementación está
dividida en parciales dentro de `Assets/script/player/`. Esta división conserva
la serialización del prefab y la API que consumen triggers, móvil, multiplayer,
skins y el Level Editor:

```text
PlayerMovement.cs                 ciclo Unity, sensores y movimiento base
PlayerMovementStateMachine.cs     estados de vida, locomoción y acción
PlayerMovement.Input.cs           Input System y control externo
PlayerMovement.Dash.cs            dash terrestre/aéreo
PlayerMovement.Punch.cs           punch
PlayerMovement.Knockback.cs       knockback
PlayerMovement.Jetpack.cs         jetpack
PlayerMovement.Swim.cs            arrastre horizontal experimental y Player_Swim
PlayerMovement.Life.cs            daño, vida, muerte y respawn
PlayerMovement.Presentation.cs    Animator y efectos visuales
PlayerMovement.Debug.cs           diagnóstico y overlay
```

`PlayerMovementStateMachine` mantiene tres dimensiones para no crear un enum con
todas las combinaciones posibles: `Alive/Dead`, `Grounded/Airborne/WallStick/
WallSlide` y las acciones `Free/DashGround/DashAir/Punch/Knockback/
ExternalLaunch` y `Swim`. Dash, punch, arrastre y knockback ya reservan y liberan acciones mediante
transiciones. Los flags históricos siguen como capa de compatibilidad mientras
se completa la migración de paredes, lanzamientos externos y física base.

Los cambios en este componente deben validarse dentro de Unity `6000.3.8f1` y
probar el prefab de jugador tanto en escenas manuales como en la cadena
`.jmap` -> `.jfue` -> `.unity`; una compilación aislada del SDK no cubre este
contrato.

## SDK

```text
Tools/jumpfall-sdk/
├── jumpfall_sdk.py
├── pyproject.toml
├── schema/
├── templates/
└── wiki/
```

El editor visual `jumpfall_menu_editor.py` fue creado y pasó su self-test como una actualización separada del SDK. La ruta prevista al integrarlo es `Tools/jumpfall-sdk/jumpfall_menu_editor.py`; no debe asumirse disponible en una rama que aún no contenga esa actualización.

### `jumpfall_sdk.py`

- valida manifiesto;
- valida árbol de archivos;
- comprueba capacidades;
- valida menús, parches, mapas y localización;
- empaqueta ZIP con extensión `.jfmod`.

### `jumpfall_menu_editor.py`

- interfaz Tkinter;
- lienzo 1920×1080;
- edición visual del JSON de menú;
- reutiliza `Validator` y `pack_command`.

## Level Editor

`ModLevelEditorRegistry` lee `content.levelEditor` de los mods activos y expone
piezas con ID aislado a `LevelPieceDatabase`. `RuntimeLevelBuilder` y los dos
controladores del editor aplican el sprite, color y escala registrados después de
instanciar el arquetipo oficial. El registro es solo de memoria y se limpia al
cerrar el runtime; no modifica el ScriptableObject base.

```text
Assets/script/player/LEVELEDITOR/
```

Archivos centrales:

- `LevelData.cs`: contrato serializado, versión 29.
- `LevelSerializationResults.cs`: resultados explícitos y rechazo de versiones futuras.
- `LevelSerializer.cs`: rutas, save/load, `.jmap`, `.jfue`, `.jsm`.
- `LevelPieceDatabase.cs`: lookup de piezas.
- `LevelPieceDatabase.asset`: IDs reales disponibles.
- `RuntimeLevelBuilder.cs`: instancia fondos, piezas, triggers, soundtrack y datos runtime.
- `RuntimeLevelBuildReport.cs`: contrato neutral y ordenado del resultado del builder.
- `LevelTriggerDatabase`: lookup de triggers.
- `PlaytestScene` y controladores del editor: interacción visual y teclas.

`RuntimeLevelBuilder.BuildWithReport` comparte la misma ruta de construcción que
`Build`. Sus fixtures neutrales, catálogo de definiciones y salida esperada están
en `Tools/jumpfall-sdk/fixtures/runtime-builder/`, para que una futura
implementación Godot pueda comprobar el mismo comportamiento sin copiar
componentes Unity.

La frontera de portabilidad y los perfiles de capacidades se documentan en
[Engine portability](Engine-Portability).

Configuración runtime:

```text
Assets/Resources/JumpfallCompiledMapRuntimeConfig
Assets/Resources/JumpfallLevelTriggerDatabase.asset
```

## Skins

```text
Assets/player/lautaro/lautaro-new-version/skinmod/
```

- `JVSKManager.cs`: carpetas, búsqueda, extracción y flags.
- `JVSKReader.cs`: lectura directa de ZIP, preview, frames y audio.
- `SkinModManager.cs`: estado del Animator, frames, fallbacks, escala, color y hot reload.
- `MenuSkinLocal.cs`: lista de `.jvsk` locales.
- `SkinSourcePolicy`: decide fuente activa y restricciones.

Workshop:

```text
Assets/integrations/Steam/MenuSkinWorkshop.cs
Assets/integrations/Steam/WorkshopSyncManager.cs
Assets/integrations/Steam/WorkshopInstaller.cs
```

## Menú principal

```text
Assets/sprites/menu/script/MainMenu.cs
```

- conecta botones base;
- New Game carga la campaña original;
- abre Level Editor, skins, Workshop y configuración;
- valida escenas antes de cargar;
- los menús `.jfmod` son una capa separada aplicada por `ModContentRuntime`.

## Fronteras de formato

- `.jfmod` no debe llamar directamente scripts internos.
- `.jvsk` solo reemplaza la presentación del jugador.
- `.jfue` solo referencia IDs registrados.
- `.jsm` solo empaqueta un mapa y assets.
- El SDK no incluye assets propietarios del juego.

## Regla de mantenimiento

Cuando cambie el contrato de modding, actualiza en el mismo cambio:

1. runtime Unity;
2. `README-MODDING.md`;
3. SDK y schema;
4. plantilla;
5. editor visual si afecta menús;
6. páginas de esta wiki;
7. pruebas automáticas.
