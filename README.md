# JumpFall SDK 1.0

Herramientas externas para crear, validar y empaquetar mods oficiales `.jfmod`
sin abrir Unity.

Esta carpeta es la fuente de la repo independiente `jumpfall-SDK`. El SDK no
incluye el juego, ejecutables, escenas ni recursos
propietarios. Para ejecutar y probar un mod se necesita una copia instalada de
JumpFall.

## Estado

El SDK mínimo incluye:

- validador del manifiesto y del contenido;
- empaquetador `.jfmod`;
- plantilla funcional;
- JSON Schema;
- páginas preparadas para GitHub Wiki;
- validación automática mediante GitHub Actions.

El runtime objetivo es JumpFall `0.50.05` con schema y SDK `1.0.0`.

Para mapas, las herramientas oficiales son el Level Editor de JumpFall y el
convertidor de desarrollo `JMAP -> .unity`. Los `.jfue` creados por el editor
pueden incluir boss graphs y grabaciones ghost-player con estados de animación; el SDK los valida y
empaqueta como parte del mapa, pero no reemplaza el editor ni convierte JMAP. El
ghost usa la apariencia del player instanciado y, en PC, la JVSK activa del
usuario; el mapa no empaqueta ni impone esa skin.

## Requisitos

- Python **3.10 o superior**;
- Windows, Linux o macOS;
- JumpFall instalado para probar el resultado.

Android e iOS no cargan `.jfmod`.

## Inicio rápido

Copia la plantilla:

```bash
cp -R templates/content-mod mi-primer-mod
```

PowerShell:

```powershell
Copy-Item -Recurse templates/content-mod mi-primer-mod
```

Edita `mi-primer-mod/jumpfall.mod.json` y cambia como mínimo:

- `id`;
- `name`;
- `version`;
- `author`;
- `description`.

Valida:

```bash
python3 jumpfall_sdk.py validate mi-primer-mod
```

Empaqueta:

```bash
python3 jumpfall_sdk.py pack mi-primer-mod
```

Salida personalizada:

```bash
python3 jumpfall_sdk.py pack mi-primer-mod -o dist/mi-mod.jfmod
```

`pack` siempre valida primero. Si existe un error, no genera el paquete.
Las advertencias se muestran aunque el paquete sea válido y llegue a crearse.
La salida debe quedar fuera de la carpeta fuente del mod; así el empaquetador no
puede intentar incluir su propio `.jfmod`.

## Probar en JumpFall

Copia el `.jfmod` en:

```text
Documentos/jumpfall/mods/packages/
```

Después:

1. Abre JumpFall en PC.
2. Presiona `F10`.
3. Pulsa `Actualizar lista`.
4. Activa el mod.
5. Pulsa `Reiniciar y aplicar`.

En Unity Editor, detén Play Mode y vuelve a iniciarlo porque el reinicio automático
está deshabilitado allí.

Argumentos de modo seguro:

```text
-safe_mode
-no_mods
-disable_mods
```

## Estructura recomendada

```text
mi-mod/
├── jumpfall.mod.json
├── content/
│   ├── maps/
│   │   └── intro.jfue
│   ├── level-editor/
│   │   └── pieces.json
│   ├── patches/
│   │   └── main-menu.json
│   ├── menus/
│   │   └── main-menu.json
│   └── localization/
│       ├── english.json
│       └── spanish-latam.json
├── assets/
│   ├── images/
│   │   └── background.png
│   └── audio/
│       └── theme.ogg
└── README.md
```

El manifiesto debe quedar directamente en la raíz del mod.

## Capacidades actuales

| Capacidad | Estado | Uso |
| --- | --- | --- |
| `maps` | funcional mínimo | Registrar mapas compilados `.jfue`. |
| `level_editor` | funcional | Agregar piezas 2D seguras a la paleta del editor. |
| `visuals` | funcional mínimo | Texto, sprites, imágenes y colores. |
| `audio` | funcional mínimo | Clips `.wav`/`.ogg` y volumen. |
| `localization` | funcional mínimo | Agregar o reemplazar claves. |
| `menus` | funcional mínimo | Capas IMGUI para main menu o pausa. |
| `mechanics` | funcional limitado | Ajustes pequeños del controlador 2D. |
| `lua` | deshabilitado | El paquete se rechaza hasta existir un sandbox probado. |

“Funcional mínimo” significa que la implementación existe en el código. Todavía
debe probarse dentro de Unity `6000.3.8f1` y en builds Standalone antes de una
publicación estable.

## Tipos de mod

### `content`

Agrega contenido o modifica elementos declarados del juego.

### `total_conversion`

Puede combinar mapas, visuales, audio, localización, menús y ajustes mecánicos.
Sigue siendo una capa sobre JumpFall:

- necesita el juego base;
- no cambia archivos instalados;
- no reemplaza el ejecutable;
- no carga DLL ni C# externo;
- no sustituye `PlayerMovement`;
- no convierte el gameplay en movimiento por un entorno 3D.

Los renders o imágenes con apariencia 3D sí pueden utilizarse como fondos 2D.
Solo puede haber una conversión completa activa.

## Manifiesto mínimo

```json
{
  "schemaVersion": "1.0.0",
  "id": "com.autor.mi-mod",
  "name": "Mi mod",
  "version": "1.0.0",
  "author": "Autor",
  "description": "Descripción",
  "type": "content",
  "gameVersion": {
    "min": "0.50.05",
    "max": ""
  },
  "priority": 0,
  "dependencies": [],
  "conflicts": [],
  "capabilities": ["visuals"],
  "content": {
    "maps": [],
    "levelEditor": [],
    "scenePatches": ["content/patches/main-menu.json"],
    "menus": [],
    "localization": [],
    "scripts": [],
    "playerTuning": {
      "moveSpeedMultiplier": 1.0,
      "jumpForceMultiplier": 1.0,
      "gravityMultiplier": 1.0,
      "dashSpeedMultiplier": 1.0,
      "maxJumpsDelta": 0
    }
  }
}
```

## Identificador

`id` debe:

- tener entre 3 y 64 caracteres;
- comenzar con una letra minúscula o número;
- usar minúsculas, números, punto, guion o guion bajo;
- permanecer igual en futuras versiones;
- no ser `jumpfall`.

Ejemplo:

```text
com.jesus.mapa-nocturno
```

## Versiones y dependencias

El mod usa SemVer:

```text
1.0.0
1.2.0-beta.1
2.0.0+build.4
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

Ejemplo:

```json
"dependencies": [
  {
    "id": "com.autor.recursos",
    "version": "^1.0.0",
    "optional": false
  }
]
```

El runtime vuelve a resolver dependencias, conflictos, ciclos y versiones antes
de activar.

## Mapas

```json
{
  "id": "intro",
  "name": "Introducción",
  "file": "content/maps/intro.jfue",
  "templateScene": "MapJfue"
}
```

El mapa debe conservar la estructura de assets creada por el Level Editor.
JumpFall copia temporalmente el paquete a un caché controlado antes de usar su
cargador existente. Nunca se autoriza una ruta arbitraria fuera del paquete.

## Piezas propias en el Level Editor

Un mod activo puede agregar piezas a la paleta sin editar los assets del juego.
Es una función exclusiva de PC. Declara:

```json
"capabilities": ["level_editor"],
"content": {
  "levelEditor": ["content/level-editor/pieces.json"]
}
```

`content/level-editor/pieces.json`:

```json
{
  "pieces": [
    {
      "id": "blue-platform",
      "name": "Blue Platform",
      "baseId": "box_ground",
      "asset": "assets/images/blue-platform.png",
      "color": "#FFFFFFFF",
      "pixelsPerUnit": 100,
      "scaleX": 2,
      "scaleY": 1
    }
  ]
}
```

Al activar el mod y reiniciar, el editor muestra `Blue Platform` y guarda
`<id-del-mod>:blue-platform` en el mapa. El prefijo impide colisiones entre mods.
El SDK comprueba también que un `.jfue` no use piezas desconocidas.

Arquetipos permitidos:

| `baseId` | Comportamiento heredado |
| --- | --- |
| `box_ground` | Plataforma y colisión de suelo. |
| `checkpoint` | Punto de control. |
| `apple` | Coleccionable/manzana del juego. |
| `orb_jump` | Orbe de salto. |
| `plane_jump` | Plataforma de impulso configurable. |
| `elevator` | Elevador 2D configurable. |

`asset` y `color` son opcionales. Usa `scaleX: 0` y `scaleY: 0` para heredar la
escala base, o define ambos entre `0.05` y `100`. Las imágenes admitidas son PNG,
JPG y JPEG, con los límites generales del SDK.

Flujo recomendado:

1. Crea y valida el catálogo.
2. Empaqueta, instala y activa el mod.
3. Reinicia JumpFall.
4. Abre Level Editor y coloca la pieza desde la paleta.
5. Prueba y compila el mapa.
6. Incluye el `.jfue` en el mismo mod.

Un mapa con estas piezas requiere el mod activo. Si falta, la pieza se omite con
un diagnóstico. No se admiten prefabs arbitrarios, componentes, scripts, 3D ni
triggers nuevos; los triggers siguen usando el catálogo oficial.

## Parches de escena

```json
{
  "patches": [
    {
      "scene": "Menugame",
      "target": "/Canvas/Title",
      "operation": "set_text",
      "value": "JumpFall modded",
      "asset": "",
      "localizationKey": "com.autor.mod.title",
      "boolValue": true,
      "numberValue": 1.0
    }
  ]
}
```

Operaciones:

- `set_active`;
- `set_text`;
- `set_sprite`;
- `set_color`;
- `set_audio_clip`;
- `set_audio_volume`.

Los selectores son rutas exactas y siempre comienzan con `/`:

```text
/Canvas/MainPanel/Title
```

Se rechazan rutas con segmentos críticos relacionados con `player`, `rigidbody`,
`collider`, `camera`, `spawn`, `loading`, `modruntime`, `modmanager`,
`eventsystem` o `inputsystem`. La comparación ignora mayúsculas, espacios y
guiones.

## Menús

Superficies:

- `main`;
- `pause`.

Elementos:

- `panel`;
- `image`;
- `text`;
- `button`.

Acciones:

- `resume`;
- `quit`;
- `load_map`;
- `set_active`;
- `toggle_active`.

No existe `load_scene`: un mod no puede cargar escenas internas arbitrarias.

Los layouts utilizan coordenadas de referencia `1920x1080`. La implementación
actual usa IMGUI y mouse; la navegación completa con mando queda pendiente.

## Localización

```json
{
  "items": [
    {
      "key": "com.autor.mod.title",
      "value": "Mi mod"
    }
  ]
}
```

Idiomas reconocidos (igual que el runtime del juego):

- `English` (alias: `en`);
- `SpanishLatam` (alias: `es`, `es-419`, `Spanish`, `spanish-latam`, `latam`, `espanol`);
- `SpanishSpain` (alias: `es-ES`, `eses`, `espanolespana`);
- `Portuguese` (alias: `pt`, `pt-BR`, `portugues`, `brazilian`).

El SDK normaliza cada idioma como el juego y rechaza duplicados tras normalizar:
`es` + `Spanish` es un duplicado (`spanishlatam`), no dos idiomas. Un idioma
desconocido produce una advertencia `localization.unknown_language` porque el
juego lo ignorará en silencio.

Seguridad añadida del validador (además de lo ya documentado):

- dimensiones reales PNG/JPEG (máx. 4096x4096 por lado, leídas de cabecera);
- firmas `RIFF/WAVE` y `OggS` en audio;
- nombres reservados de Windows (`CON`, `PRN`, `COM1`…), puntos/espacios finales
  y colisiones sin distinguir mayúsculas;
- rangos de dependencia con la misma gramática del runtime (`*`, `^`, `~`,
  `>=`, `||`, wildcards `1.2.x`);
- aviso si `gameVersion` queda fuera de la versión conocida por el SDK;
- versión del mapa (rechaza futuro, avisa legacy) y límites de bosses
  (8 por mapa, 128 nodos);
- `scene`, `value`, `localizationKey` y color `#RRGGBB(AA)` en parches
  (el runtime ignora colores inválidos sin avisar);
- paquetes `.jfmod` deterministas (mismo hash si el contenido no cambia;
  `SOURCE_DATE_EPOCH` para fijar la fecha).

## Ajustes del jugador

```json
"playerTuning": {
  "moveSpeedMultiplier": 1.05,
  "jumpForceMultiplier": 1.0,
  "gravityMultiplier": 1.0,
  "dashSpeedMultiplier": 1.0,
  "maxJumpsDelta": 0
}
```

Límites:

| Campo | Rango |
| --- | --- |
| multiplicadores | `0.75` a `1.25` |
| `maxJumpsDelta` | `-1`, `0` o `1` |

Al combinar varios mods, el resultado final vuelve a limitarse al mismo rango.

## Seguridad

El SDK y el runtime rechazan:

- rutas absolutas y `..`;
- enlaces simbólicos dentro del paquete;
- DLL, ejecutables, C#, scripts del sistema y código nativo;
- AssetBundles;
- más de 2000 archivos;
- paquetes o archivos sobre sus límites;
- capacidades desconocidas;
- Lua hasta que exista el sandbox oficial.
- cualquier archivo `.lua`, incluso si no está declarado en el manifiesto.

Límites:

| Elemento | Máximo |
| --- | --- |
| `.jfmod` comprimido | 256 MiB |
| contenido extraído | 512 MiB |
| archivo individual | 128 MiB |
| imagen | 32 MiB y 4096x4096 al decodificar |
| audio | 64 MiB |
| mapa `.jfue` | 16 MiB |
| manifiesto | 256 KiB |

Un mapa puede contener como máximo 10000 piezas, 2000 triggers, 256 fondos y 256
pistas. Lua se fuerza a desactivado en la copia temporal de cualquier mapa
cargado desde `.jfmod`.

El manifiesto admite hasta 128 mapas, 16 archivos de Level Editor, 32 archivos de
parches, 16 archivos de menús y 16 archivos de localización. Cada mod puede
registrar como máximo 512 piezas del editor; el runtime limita el total activo a
4096.

## Códigos de salida

- `0`: validación o empaquetado correcto;
- `1`: contenido inválido;
- `2`: uso incorrecto de la CLI.

## Publicación como repo independiente

La repo `jumpfall-SDK` debe conservar:

```text
README.md
jumpfall_sdk.py
pyproject.toml
templates/
schema/
tests/
wiki/
```

GitHub Wiki utiliza su propio repositorio Git. Las páginas dentro de `wiki/` son
la fuente que debe sincronizarse con ella.

## Mantenimiento

Un cambio del contrato debe actualizar conjuntamente:

1. runtime de JumpFall;
2. `README-MODDING.md`;
3. este README;
4. validador y empaquetador;
5. JSON Schema;
6. plantillas;
7. wiki;
8. README principal del proyecto cuando cambie el estado general.

No documentes como terminada una capacidad que todavía no haya sido compilada y
probada en una build real.


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
