# Menús y parches de escena

## Menús declarativos

Los menús de mods usan una referencia de `1920×1080`. El runtime escala y centra el contenido en otras resoluciones.

### Estructura

```json
{
  "menus": [
    {
      "id": "mi-menu",
      "surface": "main",
      "scene": "Menugame",
      "hideTargets": [],
      "sortingOrder": 500,
      "elements": []
    }
  ]
}
```

### Coordenadas

- `x = 0`, `y = 0`: centro de pantalla.
- `x` positivo: derecha.
- `y` positivo: arriba.
- Los hijos se posicionan respecto al centro del padre.
- El padre debe aparecer antes que sus hijos en el array.

### Elemento completo

```json
{
  "id": "play-button",
  "parent": "panel",
  "type": "button",
  "text": "Jugar",
  "localizationKey": "com.autor.mod.play",
  "asset": "",
  "color": "#FFFFFFFF",
  "x": 0,
  "y": -120,
  "width": 360,
  "height": 72,
  "fontSize": 30,
  "action": "load_map",
  "target": "intro",
  "value": ""
}
```

### Tipos

#### `panel`

Dibuja una caja con color. Úsalo como fondo o padre.

#### `image`

Carga PNG/JPG/JPEG desde el paquete.

#### `text`

Dibuja texto centrado con salto de línea.

#### `button`

Dibuja un botón y ejecuta una acción permitida.

### Acciones

| Acción | Uso |
| --- | --- |
| vacío | Elemento sin interacción. |
| `resume` | Restaura `Time.timeScale = 1`. |
| `quit` | Cierra la aplicación. |
| `load_map` | Carga un ID declarado en `content.maps`. |
| `set_active` | Activa o desactiva un objeto de la escena según `value`. |
| `toggle_active` | Alterna el estado del objeto objetivo. |

No existe `load_scene`.

### `hideTargets`

Rutas exactas que comienzan con `/`:

```json
"hideTargets": [
  "/Canvas/MainPanel"
]
```

No existen comodines. Si la ruta no coincide exactamente, el runtime genera `menu.target_missing` o conserva el menú base.

## Parches de escena

```json
{
  "patches": [
    {
      "scene": "Menugame",
      "target": "/Canvas/MainPanel/Title",
      "operation": "set_text",
      "value": "JumpFall modded",
      "asset": "",
      "localizationKey": "",
      "boolValue": true,
      "numberValue": 1.0
    }
  ]
}
```

Operaciones:

```text
set_active
set_text
set_sprite
set_color
set_audio_clip
set_audio_volume
```

### Selectores

Correcto:

```text
/Canvas/MainPanel/Title
```

Incorrecto:

```text
Canvas/MainPanel/Title
```

Los nombres y mayúsculas deben coincidir. En una build distinta la jerarquía puede cambiar; un parche ausente produce advertencia y el resto del mod continúa.

También se bloquean rutas cuyos segmentos señalen sistemas críticos: jugador,
Rigidbody, Collider, cámara, spawn, carga, runtime/gestor de mods, EventSystem e
InputSystem. Usa parches solo sobre UI y objetos visuales declarados como seguros.

## Recomendaciones

- Mantén siempre una forma de jugar, volver o salir.
- No ocultes el menú base hasta haber probado tu capa.
- Evita llenar toda la pantalla con un único botón sin fallback.
- Usa el editor visual para reducir errores de posición y orden de padres.
- Prueba 1280×720, 1920×1080 y una resolución ultrawide.
