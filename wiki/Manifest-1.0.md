# Manifiesto `jumpfall.mod.json` 1.0

El manifiesto identifica el paquete y registra todo su contenido.

## Ejemplo completo

```json
{
  "schemaVersion": "1.0.0",
  "id": "com.autor.campana-nocturna",
  "name": "Campaña nocturna",
  "version": "1.0.0",
  "author": "Autor",
  "description": "Campaña, menú y música nocturna.",
  "type": "total_conversion",
  "gameVersion": {
    "min": "0.50.05",
    "max": ""
  },
  "priority": 200,
  "dependencies": [],
  "conflicts": [],
  "capabilities": [
    "maps",
    "level_editor",
    "visuals",
    "audio",
    "localization",
    "menus",
    "mechanics"
  ],
  "content": {
    "maps": [
      {
        "id": "intro",
        "name": "Introducción",
        "file": "content/maps/intro.jfue",
        "templateScene": "MapJfue"
      }
    ],
    "levelEditor": [
      "content/level-editor/pieces.json"
    ],
    "scenePatches": [
      "content/patches/main-menu.json"
    ],
    "menus": [
      "content/menus/main-menu.json"
    ],
    "localization": [
      {
        "language": "English",
        "file": "content/localization/en.json"
      },
      {
        "language": "SpanishLatam",
        "file": "content/localization/es-419.json"
      }
    ],
    "scripts": [],
    "playerTuning": {
      "moveSpeedMultiplier": 1.05,
      "jumpForceMultiplier": 1.0,
      "gravityMultiplier": 1.0,
      "dashSpeedMultiplier": 1.0,
      "maxJumpsDelta": 0
    }
  }
}
```

## Campos principales

| Campo | Obligatorio | Regla |
| --- | --- | --- |
| `schemaVersion` | Sí | Debe ser exactamente `1.0.0`. |
| `id` | Sí | ID estable y único. |
| `name` | Sí | Nombre visible, máximo 128 caracteres. |
| `version` | Sí | SemVer. |
| `author` | Sí | Máximo 128 caracteres. |
| `description` | Recomendado | Máximo 4096 caracteres. |
| `type` | Sí | `content` o `total_conversion`. |
| `gameVersion` | Sí | Incluye `min`; `max` puede estar vacío. |
| `priority` | No | Entero entre `-1000` y `1000`. |
| `dependencies` | No | Mods necesarios u opcionales. |
| `conflicts` | No | Combinaciones bloqueadas. |
| `capabilities` | Sí | Solo capacidades realmente utilizadas. |
| `content` | Sí | Registro explícito del contenido. |

## Compatibilidad del juego

```json
"gameVersion": {
  "min": "0.50.05",
  "max": ""
}
```

Un `max` vacío significa “sin máximo declarado”, no “compatibilidad eterna garantizada”. Para una primera prueba estricta puedes usar:

```json
"gameVersion": {
  "min": "0.50.05",
  "max": "0.50.05"
}
```

## Dependencias

```json
"dependencies": [
  {
    "id": "com.autor.recursos",
    "version": "^1.0.0",
    "optional": false
  }
]
```

Rangos comprendidos por el runtime:

```text
*
1.2.3
>=1.2.0 <2.0.0
^1.2.0
~1.2.0
1.2.x
^1.0.0 || ^2.0.0
```

Una dependencia obligatoria se resuelve antes que el mod consumidor. Las opcionales no se activan automáticamente.

## Conflictos

```json
"conflicts": [
  {
    "id": "com.otro.menu",
    "version": "*",
    "reason": "Los dos reemplazan el menú principal."
  }
]
```

Declara conflicto cuando la combinación no tenga sentido, no solamente cuando ambos toquen algo parecido.

## Orden de carga

1. Dependencias antes que consumidores.
2. Prioridad entre mods sin relación directa.
3. ID como desempate determinista.

La prioridad no rompe ciclos ni ignora conflictos.

## Paths

Todos los paths son relativos a la raíz del paquete:

```json
"file": "content/maps/intro.jfue"
```

No se permiten:

```text
C:\mods\archivo.png
/home/user/mods/archivo.png
../archivo.png
```

La capitalización importa especialmente en Linux.

## `content.maps`

```json
{
  "id": "castillo",
  "name": "Castillo",
  "file": "content/maps/castillo.jfue",
  "templateScene": "MapJfue"
}
```

`templateScene` debe ser `MapJfue`.

## `content.levelEditor`

Lista archivos JSON que registran piezas 2D seguras en la paleta del editor:

```json
"levelEditor": [
  "content/level-editor/pieces.json"
]
```

Si la lista no está vacía, `capabilities` debe incluir `level_editor`. El campo es
opcional para manifiestos anteriores y se normaliza a una lista vacía. Consulta
[Piezas de mods en Level Editor](Custom-Level-Editor-Pieces).

## `content.scenePatches`

Array de rutas JSON:

```json
"scenePatches": [
  "content/patches/main-menu.json"
]
```

## `content.menus`

```json
"menus": [
  "content/menus/main-menu.json",
  "content/menus/pause.json"
]
```

## `content.localization`

```json
{
  "language": "SpanishLatam",
  "file": "content/localization/es-419.json"
}
```

Idiomas principales: `English` y `SpanishLatam`.

## `content.scripts`

Debe permanecer vacío:

```json
"scripts": []
```

Cualquier script o capacidad Lua se rechaza en Modding 1.0.

## `playerTuning`

```json
"playerTuning": {
  "moveSpeedMultiplier": 1.15,
  "jumpForceMultiplier": 1.10,
  "gravityMultiplier": 0.85,
  "dashSpeedMultiplier": 1.20,
  "maxJumpsDelta": 1
}
```

Rangos:

| Campo | Rango |
| --- | --- |
| multiplicadores | `0.75` a `1.25` |
| `maxJumpsDelta` | `-1`, `0`, `1` |

El resultado compuesto de varios mods vuelve a limitarse al mismo rango.
