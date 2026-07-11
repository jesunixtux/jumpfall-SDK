# Referencia del formato de mapas

La clase fuente es `Assets/script/player/LEVELEDITOR/LevelData.cs`.

## Versión

```text
LevelData.CurrentVersion = 16
```

Al cargar, `Normalize()` corrige listas nulas, valores antiguos y actualiza la versión.

## `LevelData`

```json
{
  "version": 16,
  "gridSize": 1.0,
  "spawnPoint": { "x": 0.0, "y": 0.0 },
  "useCustomPlayerGravity": true,
  "playerGravityScale": 3.25,
  "background": {},
  "backgrounds": [],
  "soundtrack": {},
  "lua": {},
  "pieces": [],
  "triggers": []
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
  "eventMessageName": "Activate",
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
send_message
destroy
```

Valores: `on`, `off`, `toggle`.

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
