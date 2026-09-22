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

La herramienta es canary/prototipo: guarda con frecuencia.

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
