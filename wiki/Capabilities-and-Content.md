# Capacidades y contenido

Las capacidades funcionan como permisos declarativos. Un mod debe declarar lo que realmente usa y el SDK rechaza contenido que necesita una capacidad ausente.

## `maps`

Registra archivos `.jfue` compilados.

```json
"maps": [
  {
    "id": "laboratorio",
    "name": "Laboratorio",
    "file": "content/maps/laboratorio.jfue",
    "templateScene": "MapJfue"
  }
]
```

El runtime copia temporalmente el árbol permitido del mod a un caché controlado dentro de la carpeta Workshop y carga el mapa con el cargador normal de JumpFall.

## `level_editor`

Registra piezas 2D del mod en la paleta del Level Editor. Cada pieza hereda un
arquetipo oficial, usa un ID aislado por el ID del mod y puede cambiar sprite,
color y escala. No permite código, prefabs arbitrarios ni comportamiento libre.

```json
"levelEditor": ["content/level-editor/pieces.json"]
```

Consulta [Piezas de mods en Level Editor](Custom-Level-Editor-Pieces) para el
contrato completo y el flujo de creación.

## `visuals`

Permite:

- `set_text`;
- `set_sprite`;
- `set_color`;
- `set_active`;
- imágenes en menús;
- paneles, textos y botones declarativos.

Formatos de imagen:

```text
.png
.jpg
.jpeg
```

Máximo: 32 MiB y 4096×4096 después de decodificar.

## `audio`

Permite reemplazar clips y volumen mediante parches.

Formatos:

```text
.wav
.ogg
```

No permite micrófono, streams de red ni enumeración de dispositivos.

## `localization`

Archivo:

```json
{
  "items": [
    {
      "key": "com.autor.mod.play",
      "value": "Jugar"
    }
  ]
}
```

Usa el ID del mod como prefijo para evitar colisiones.

## `menus`

Crea capas IMGUI independientes de prefabs concretos.

Superficies:

```text
main
pause
```

Tipos de elemento:

```text
panel
image
text
button
```

Acciones:

```text
resume
quit
load_map
set_active
toggle_active
```

La navegación completa con mando todavía no está implementada.

## `mechanics`

Modifica campos existentes de `PlayerMovement` dentro de límites estrictos:

- velocidad;
- salto;
- gravedad;
- dash;
- saltos máximos.

No permite sustituir el controlador ni añadir lógica arbitraria.

## Capacidades no disponibles

### Lua

`.jfmod` rechaza Lua. Aunque el formato histórico de mapas contiene campos y carpetas Lua, Modding 1.0 no debe anunciarlo como una función disponible.

### Armas u objetos con código nuevo

Un mod no puede crear por sí solo:

- apuntado;
- proyectiles nuevos;
- munición;
- recarga;
- inteligencia artificial;
- nuevos callbacks C#.

Para permitirlo de forma segura, JumpFall debe incorporar primero un sistema genérico en el juego base y exponer definiciones JSON limitadas. Consulta [Extender JumpFall](Extending-JumpFall).
