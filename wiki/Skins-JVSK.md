# Skins visuales `.jvsk`

`.jvsk` significa JumpFall Visual Skin Kit. Es un ZIP que contiene `skin.json`, carpetas de frames PNG y metadatos opcionales.

Las skins son un sistema separado de `.jfmod`.

## Plataformas

Las skins personales están habilitadas solamente cuando compila `UNITY_STANDALONE`:

- Windows;
- macOS;
- Linux.

Android e iOS restauran el sprite base y deshabilitan el sistema personal.

## Carpetas

```text
Documentos/jumpfall/skin/
├── local/
├── workshop/
└── temp_extract/
```

- `local`: archivos `.jvsk` instalados manualmente.
- `workshop`: paquetes obtenidos desde Workshop.
- `temp_extract`: extracción segura usada por el runtime.

## Estructura recomendada

```text
mi-skin.jvsk
├── skin.json
├── meta.json
├── preview.png
├── idle/
│   ├── 000.png
│   └── 001.png
├── walk/
├── run/
├── jump/
├── fly/
├── punch/
├── landing/
├── death/
├── dashground/
├── dashair/
├── climbingwall/
└── climbingwalljump/
```

Usa nombres de frame con ceros a la izquierda. El cargador extraído ordena archivos alfabéticamente; `1.png, 2.png, 10.png` puede quedar en un orden inesperado.

## `skin.json`

```json
{
  "active": false,
  "fps": 12,
  "visual": {
    "scale": 1.0,
    "widthScale": 1.0,
    "heightScale": 1.0,
    "mirror": true,
    "colorOverlay": [255, 255, 255, 255]
  },
  "files": {
    "idle": {
      "path": "idle",
      "fps": 12,
      "pivotX": 0.5,
      "pivotY": 0.0,
      "xOffset": 0.0,
      "yOffset": 0.0,
      "loop": true
    },
    "walk": {
      "path": "walk",
      "fps": 12,
      "pivotX": 0.5,
      "pivotY": 0.0,
      "xOffset": 0.0,
      "yOffset": 0.0,
      "loop": true
    }
  }
}
```

## Campos globales

### `active`

Bandera histórica que `JVSKManager` puede modificar dentro del ZIP. La selección moderna también se conserva mediante `PlayerPrefs` y `SkinSourcePolicy`.

### `fps`

FPS por defecto cuando un estado no define FPS propio.

### `visual.scale`

Escala uniforme.

### `widthScale` / `heightScale`

Ajustes independientes.

### `mirror`

Permite reflejar según la escala del padre cuando `mirrorByParentScale` está activo.

### `colorOverlay`

RGBA de `0` a `255`.

## Estados admitidos

```text
idle
walk
run
jump
fly
punch
landing
death
dashground
dashair
climbingwall
climbingwalljump
```

Alias normalizados:

```text
dash_ground -> dashground
dash_air -> dashair
climbing_wall -> climbingwall
climbing_wall_jump -> climbingwalljump
climbingWall -> climbingwall
climbingWallJump -> climbingwalljump
```

## Estados del Animator reconocidos

El runtime detecta, entre otros:

```text
Player_Idle
Player_Walk
Player_Run
Player_Jump
Player_Fly
Player_Punch
Player_Landing
Player_Death
Player_dash_ground
Player_Dash_Fly
Player_ClimbingWall
Player_ClimbingWall_Jump
```

También reconoce variantes históricas para punch y wall slide.

## Fallbacks

Si falta un estado, el runtime intenta otro:

- Walk → Run → Idle.
- Run → Walk → Idle.
- Jump → Fly → Idle.
- Fly → Jump → Idle.
- Landing → Jump → Idle.
- DashGround → Run → Walk → Idle.
- DashAir → Jump → Fly → Idle.
- ClimbingWall → Jump → Idle.
- ClimbingWallJump → Jump → ClimbingWall → Idle.
- Punch/Death → Idle.

Si no hay frames utilizables, se muestra el renderer base.

## Loop

Estos estados se fuerzan como no-loop por defecto:

```text
jump
landing
punch
death
climbingwalljump
```

## Pivot y offsets

- `pivotX` / `pivotY`: pivot normalizado del sprite.
- `xOffset` / `yOffset`: desplazamiento dividido por 100 al aplicar.
- PPU en el cargador principal: `100`.

## `meta.json`

Opcional para Workshop:

```json
{
  "mod_name": "Mi skin",
  "title": "Mi skin",
  "author": "Autor",
  "description": "Descripción",
  "version": "1.0.0",
  "preview": "preview.png",
  "workshop_id": 1234567890
}
```

El menú Workshop usa `mod_name` o `title` y carga la ruta indicada en `preview`.

## Instalar localmente

Copia:

```text
mi-skin.jvsk
```

A:

```text
Documentos/jumpfall/skin/local/
```

Abre el menú de skins locales y actualiza.

## Workshop

El sincronizador instala en `skin/workshop`, luego `JVSKManager` extrae de forma segura a `temp_extract/{skinName}`. El menú Workshop muestra preview, permite avanzar con flechas, activar y desactivar.

## Hot reload

`SkinModManager` puede recargar con `F5` si `allowHotReload` está activo. Usa Input System cuando está disponible y solo recurre a input legacy si el proyecto lo habilita.

## Seguridad y rendimiento

- Paquete extraído en staging y movido al destino al completar.
- Extensiones controladas por `UserContentSafety`.
- Límite de frames por estado.
- Imágenes cargadas con validación de tamaño/dimensiones.
- Recursos temporales se destruyen al cambiar o desactivar skin.

## Problemas comunes

### La skin no aparece

- Debe terminar en `.jvsk`.
- Debe estar en `skin/local` o Workshop.
- `skin.json` debe existir en la raíz del ZIP.

### Animación desordenada

Renombra frames:

```text
000.png
001.png
002.png
```

### Se ve desplazada

Ajusta `pivotX`, `pivotY`, `xOffset` y `yOffset`.

### Solo se ve el player original

El estado actual no tiene frames válidos o el paquete fue rechazado. Revisa logs.
