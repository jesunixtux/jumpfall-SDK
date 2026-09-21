# Referencia del formato de mapas

La clase fuente es `Assets/script/player/LEVELEDITOR/LevelData.cs`.

## Versión

```text
LevelData.CurrentVersion = 29
```

Al cargar, `Normalize()` corrige listas nulas, valores antiguos y actualiza la versión.

## `LevelData`

```json
{
  "version": 29,
  "gridSize": 1.0,
  "spawnPoint": { "x": 0.0, "y": 0.0 },
  "useCustomPlayerGravity": true,
  "playerGravityScale": 3.25,
  "background": {},
  "backgrounds": [],
  "soundtrack": {},
  "lua": {},
  "pieces": [],
  "triggers": [],
  "bosses": [],
  "ghosts": []
}
```

### Gravedad

Rango aceptado por el modelo:

```text
0.0 a 12.0
```

Default:

```text
3.25
```

## `BackgroundData`

```json
{
  "enabled": true,
  "fileName": "background.png",
  "px": 0.0,
  "py": 0.0,
  "rotZ": 0.0,
  "sx": 1.0,
  "sy": 1.0,
  "pixelsPerUnit": 100.0,
  "sortingOrder": -1000
}
```

El runtime limita el sorting order para mantener el fondo detrás del gameplay.

## `SoundtrackData`

```json
{
  "enabled": true,
  "loop": true,
  "tracks": [
    {
      "fileName": "tema.ogg",
      "volume": 0.8
    }
  ]
}
```

Los nombres son archivos, no rutas externas.

## `LuaModData`

```json
{
  "enabled": false,
  "entryFile": "main.lua",
  "allowInWorkshop": true
}
```

Este campo existe en el formato histórico de mapas. No significa que Lua esté disponible para `.jfmod`.

## `PieceData`

Campos comunes:

```json
{
  "id": "box_ground",
  "px": 0.0,
  "py": 0.0,
  "rotZ": 0.0,
  "sx": 1.0,
  "sy": 1.0
}
```

IDs actuales:

```text
box_ground
checkpoint
apple
orb_jump
plane_jump
elevator
```

### Campos `plane_jump`

```json
{
  "planeJumpConfigured": true,
  "planeJumpUseWorldTarget": false,
  "planeJumpTargetX": 6.0,
  "planeJumpTargetY": 4.0,
  "planeJumpFlightTime": 1.1,
  "planeJumpControlLockSeconds": 0.2,
  "planeJumpCooldownSeconds": 0.35,
  "planeJumpMaxLaunchSpeed": 90.0,
  "planeJumpResetAirActions": true,
  "planeJumpIgnoreGravityDuringLaunch": false
}
```

Normalización:

- flight time mínimo `0.05`;
- lock y cooldown mínimo `0`;
- max speed mínimo `1`.

### Campos `elevator`

```json
{
  "elevatorConfigured": true,
  "elevatorTravelY": 4.0,
  "elevatorSpeed": 2.0,
  "elevatorWaitAtStartSeconds": 0.5,
  "elevatorWaitAtEndSeconds": 0.5,
  "elevatorStartAtEnd": false,
  "elevatorStartMovingToEnd": true,
  "elevatorLoop": true,
  "elevatorCarryRiders": true,
  "elevatorActivateOnPlayerTop": true
}
```

## `TriggerData`

Campos base:

```json
{
  "id": "finish_level",
  "px": 0.0,
  "py": 0.0,
  "rotZ": 0.0,
  "sx": 1.0,
  "sy": 1.0,
  "targetMapName": "",
  "finishAction": "menu",
  "menuSceneName": "Menugame"
}
```

IDs actuales:

```text
limit_map
deathzone
changelevel
finish_level
lua_event
static_camera
visibility
event
timer
wall_jump
```

### `changelevel`

```json
"targetMapName": "castle_02"
```

Escribe el nombre sin `.jfue`.

### `finish_level`

```json
{
  "finishAction": "menu",
  "menuSceneName": "Menugame"
}
```

La escena de menú se normaliza a `Menugame`.

### Cámara

```json
{
  "cameraViewMode": 0,
  "cameraWorldX": 0.0,
  "cameraWorldY": 0.0,
  "cameraOffsetX": 0.0,
  "cameraOffsetY": 0.0,
  "cameraOverrideOrthographicSize": false,
  "cameraOrthographicSize": 8.0,
  "cameraBlendSeconds": 0.18
}
```

### Visibilidad

```json
{
  "visibilityTargetName": "apple",
  "visibilityAction": "show",
  "visibilitySetInitialState": true,
  "visibilityInitiallyVisible": false,
  "visibilityOnlyOnce": true,
  "visibilityDisableAfterUse": true
}
```

Acciones: `show`, `hide`, `toggle`.

### Evento genérico

```json
{
  "eventTargetName": "door",
  "eventAction": "set_active",
  "eventValue": "on",
  "eventAnimatorParameter": "Open",
  "eventAnimatorStateName": "DoorOpen",
  "eventId": "ghost.restart",
  "eventDelaySeconds": 0.0,
  "eventOnlyOnce": true,
  "eventDisableAfterUse": true
}
```

Acciones normalizadas:

```text
set_active
set_renderer
set_collider
animator_trigger
animator_bool
animator_play
level_event
```

Valores: `on`, `off`, `toggle`.

`send_message` y `destroy` son valores heredados bloqueados. No deben escribirse
en mapas nuevos. `level_event` solo entrega IDs normalizados a componentes que
implementan `ILevelEventReceiver`.

El trigger `timer` usa los mismos campos, fuerza `eventAutoStart: true` y admite
un retraso entre `0` y `3600` segundos.

## `GhostPlayerData`

Ejemplo abreviado:

```json
{
  "objectId": "ghost_a1b2c3",
  "displayName": "tutorial_first_jump",
  "autoPlay": false,
  "loop": true,
  "visible": true,
  "startDelay": 0.0,
  "playbackSpeed": 1.0,
  "opacity": 0.45,
  "sortingOrder": 120,
  "sampleInterval": 0.0333333,
  "frames": [
    {
      "time": 0.0,
      "px": 1.0,
      "py": 2.0,
      "rotZ": 0.0,
      "sx": 1.0,
      "sy": 1.0,
      "flipX": false,
      "flipY": false,
      "animatorStateHash": 123456789,
      "animatorNormalizedTime": 0.35
    }
  ]
}
```

La lista raíz `ghosts` admite hasta 32 entradas. Cada entrada admite hasta
18.000 frames y 600 segundos. `displayName` se normaliza y se vuelve único para
que los triggers no activen varios ghosts por accidente. Los eventos admitidos
son `ghost.play`, `ghost.restart`, `ghost.pause`, `ghost.resume`, `ghost.stop`,
`ghost.reset`, `ghost.show`, `ghost.hide` y `ghost.toggle`.

Desde v29, `animatorStateHash` y `animatorNormalizedTime` conservan el estado
visual del Animator del prefab oficial. El runtime verifica que el estado exista
antes de reproducirlo; no ejecuta scripts del player.

Los creadores deben generar estos datos desde Ghost Player Studio. Editar a mano
puede producir trayectorias inválidas, aunque el cargador aplique límites.

## Assets relativos

Para un mapa instalado junto con assets:

```text
mapa.jfue
assetlocal/
├── backgroundimg/
├── sound/
└── lua/
```

El cargador también acepta `assetslocal` como compatibilidad antigua, pero herramientas nuevas deben escribir `assetlocal`.


## Iluminación dinámica opcional en mapas v29

`lights` contiene el contrato propio `LightData`: identidad, nombre, `px/py/rotZ`,
`startsOn`, `shape` (radial/spot/rectangle/freeform), dimensiones, `range`,
intensidad, color RGBA, falloff, radios/ángulos internos, orden, blend style y
vértices locales normalizados. `range` es el radio exterior en Radial/Spot y la
distancia de borde en Rectangle/Freeform. No hay referencias Unity en el JSON.
`lightingEnabled` ausente conserva el modo clásico; `lights` ausente/null es vacío.

Un trigger `id: "light"` reutiliza `eventAction: "set_light"`,
`eventTargetObjectId` y `eventValue: "on" | "off" | "toggle"`. El destino se resuelve
solo dentro del mapa. Un destino perdido no ejecuta nada y avisa una vez.
IDs duplicados se reparan; los destinos ambiguos quedan vacíos para reasignarlos.
No se cambia la versión del mapa ni el manifiesto `.jfmod`.

Los paquetes de mods aceptan hasta 256 luces. Runtime y SDK comparten ese límite;
el editor no trunca silenciosamente listas al guardar. El ejemplo optativo está
en `Tools/jumpfall-sdk/templates/content-mod/examples/lighting.jfue` (desde la raíz
del repositorio); no se incorpora automáticamente a `content.maps` de la plantilla.
El JSON Schema incluye los campos de iluminación y el reporte de construcción
admite registros `kind: "light"`.

Los mapas con luces deben editarse con una versión del juego que soporte estas
extensiones opcionales. La edición avanzada se hace desde Ctrl + L en PC; el
editor multiplataforma conserva estos objetos protegidos. No se añaden Lua,
scripts externos, sombras ni sincronización de red.
