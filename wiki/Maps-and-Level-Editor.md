# Mapas y Level Editor

## Los cuatro formatos

| Formato | Función |
| --- | --- |
| `.jmap` | Fuente editable del mapa. |
| `.jfue` | Mapa compilado y jugable. |
| `.jsm` | Paquete de Workshop con `.jfue` y assets. |
| `.jfmod` | Mod general que puede registrar uno o varios `.jfue`. |

No renombres una extensión para convertir un formato en otro.

## Abrir el Level Editor

1. Abre JumpFall.
2. En el menú principal selecciona **Level Editor**.
3. Se abre una escena con grilla y controles de edición.

El Level Editor y el convertidor `JMAP -> .unity` son las herramientas oficiales
de creación de mapas. Una función de mapa debe conservarse en JMAP, JFUE y en la
escena Unity convertida. Guarda con frecuencia.

## Controles principales

### Cámara

- Flechas: mover vista.
- Mouse cerca del borde: desplazar.
- Rueda: zoom.
- Click derecho + arrastrar: pan.
- `F2`: cámara libre.
- `Ctrl + G`: física/gravedad del mapa.

### Piezas

- Click izquierdo: colocar.
- Arrastrar con izquierdo: pintar.
- Click derecho: borrar.
- `Q` / `E`: rotar.
- `[` / `]`: pieza anterior/siguiente.
- `1`–`9`: selección rápida.
- `Ctrl + Z` / `Ctrl + Y`: deshacer/rehacer.

### Editar objetos

- `F4`: modo de selección y transformación.
- Arrastrar: mover.
- Handles amarillos: cambiar tamaño.
- Handle verde: mover grupo.
- `Ctrl + click`: selección múltiple.
- `Ctrl + C` / `Ctrl + V`: copiar/pegar.

### Triggers

- `F6`: entrar o salir del modo triggers.
- `F4` + `E`: configurar un trigger existente.

### Spawn

- `T`: colocar spawn en el mouse.
- `M`: modo de mover spawn.

### Playtest

- `F5`: alternar editor/jugador.
- `Home`: reset de cámara de playtest.

### Guardar y compilar

- `F7`: guardar `.jmap` editable.
- `F8`: compilar `.jfue` o preparar `.jsm`.
- `F9`: cargar `.jmap`.
- `F10`: banda sonora.
- `Ctrl+L`: abrir el panel de iluminacion del mapa.
- `F12`: abrir Ghost Player Studio o terminar una grabación.

## Piezas base registradas

La base `LevelPieceDatabase.asset` contiene:

```text
box_ground
checkpoint
apple
orb_jump
plane_jump
elevator
```

En PC, un `.jfmod` activo puede ampliar esta lista con piezas 2D basadas en esos
arquetipos. Aparecen en la paleta y se guardan con el ID
`<id-del-mod>:<id-de-pieza>`. Consulta
[Piezas de mods en Level Editor](Custom-Level-Editor-Pieces).

El editor omite piezas cuyo catálogo no está registrado. Activa el mod y reinicia
antes de abrir o compilar un mapa que las utilice.

## Triggers registrados actuales

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

El editor omite triggers no registrados. Los mods no pueden registrar triggers
nuevos en el contrato 1.0; deben reutilizar esta lista oficial.

## `plane_jump`

Placa de impulso 2D configurable:

- destino relativo o mundial;
- tiempo de vuelo;
- bloqueo temporal de controles;
- cooldown;
- velocidad máxima;
- reset de acciones aéreas;
- opción de ignorar gravedad durante el lanzamiento guiado.

En modo guiado puede bloquear movimiento, salto, dash y jetpack hasta aterrizar.

## `elevator`

Parámetros:

- desplazamiento vertical;
- velocidad;
- espera en cada extremo;
- posición inicial;
- dirección inicial;
- loop;
- transportar jugador;
- activarse al subir encima.

Durante edición permanece quieto; funciona al probar y compilar.

## Ghost-player

Ghost Player Studio graba el movimiento del jugador durante el playtest y lo
reproduce como una entidad visual sin físicas ni colisiones. Abre el panel con
`F12` o `GHOST`, crea una grabación, juega el recorrido y presiona `F12` para
guardarla.

El panel consume sus clics y pausa la cámara de edición. Cada muestra v29 guarda
posición, orientación y estado/tiempo del Animator, por lo que el movimiento
automático conserva las animaciones del player de manera determinista.

El runtime copia solo la raíz visual del player realmente instanciado, no el
prefab contenedor con UI, cámaras, físicas o audio. Esto admite sustituciones
visuales compatibles de mods. En PC muestrea también la JVSK local/Workshop
activa; la skin pertenece al usuario y no se serializa dentro de `.jmap`/`.jfue`.
En móvil se conserva la skin base.

Configuración disponible:

- reproducción automática o activación por trigger;
- loop indefinido o una sola reproducción;
- espera inicial, velocidad, opacidad y sorting order;
- frecuencia de captura de 4 a 60 FPS;
- máximo 32 ghosts por mapa y 18.000 frames por ghost.

Un trigger `event` o `timer` puede seleccionar el nombre único del ghost como
destino, usar la acción `level_event` y enviar `ghost.play`, `ghost.restart`,
`ghost.pause`, `ghost.resume`, `ghost.stop`, `ghost.reset`, `ghost.show`,
`ghost.hide` o `ghost.toggle`.

Los datos viven dentro de `.jmap`/`.jfue`. Un mod que registra ese `.jfue` no
necesita declarar otra capacidad: `maps` es suficiente.

## Fondos

`F3` abre el panel de fondos.

Carpeta local:

```text
Documentos/jumpfall/levels/assetslocal/backgroundimg/
```

- PNG.
- Puede haber varios fondos.
- Cada uno guarda posición, rotación, escala, pixels per unit y sorting order.
- No tiene collider.
- Se fuerza detrás del jugador.

## Audio

`F10` abre la banda sonora.

Carpeta:

```text
Documentos/jumpfall/levels/assetslocal/sound/
```

Formatos:

```text
.wav
.ogg
```

Cada pista tiene volumen `0`–`1`, orden y reproducción en loop opcional.

## Gravedad del mapa

`Ctrl + G` permite guardar gravedad propia. El valor recomendado actual es `3.25`.

La gravedad se serializa dentro de `.jmap` y `.jfue`.

## Iluminacion del mapa

`Ctrl + L` abre `LIGHTING SETTINGS`.

- `Enable Lighting` guarda la bandera `lightingEnabled`.
- `Ambient Light` guarda `ambientLightIntensity` entre `0` y `2`.
- Los mapas antiguos sin esas propiedades cargan como `lightingEnabled = false`
  y `ambientLightIntensity = 1`.
- Cuando la iluminacion esta desactivada, el mapa usa una Global Light 2D a
  intensidad completa para mantener el aspecto clasico.
- Cuando esta activada, `MapLightingController` aplica la intensidad ambiental
  al cargar `.jmap`, ejecutar playtest F5, cargar `.jfue` o convertir a `.unity`.

La configuracion se serializa dentro de `.jmap` y `.jfue`. El editor
multiplataforma conserva esos valores aunque su UI de iluminacion todavia es
minima.

## Carpetas

```text
Documentos/jumpfall/levels/creations/   # .jmap
Documentos/jumpfall/levels/compilator/  # .jfue
Documentos/jumpfall/levels/assetslocal/  # assets locales
Documentos/jumpfall/levels/workshop/    # mapas instalados o empaquetados
```

## Usar un mapa en `.jfmod`

1. Compila con `F8`.
2. Copia el `.jfue` a `content/maps/`.
3. Conserva la estructura `assetlocal` generada.
4. Decláralo en `content.maps`.
5. Crea un botón `load_map` o una campaña.
6. Valida y empaqueta.

## Regla crítica

Un `.jfue` es JSON y puede escribirse manualmente, pero no deberías hacerlo para un mapa normal. La escala serializada se interpreta en relación con los prefabs reales. Un mapa puede ser sintácticamente válido y cargar, pero tener plataformas gigantes, colliders incorrectos o un spawn roto. El Level Editor conoce las bases y escalas correctas.

Para niveles oficiales, usa `Jumpfall > Level Editor > Convert .jmap to .unity`.
El convertidor reconstruye también bosses, ghost-players y sus triggers.


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
