# Editor visual de menús

`jumpfall_menu_editor.py` es una herramienta de escritorio preparada y auto-probada como actualización separada para `jumpfall-sdk`. Genera el mismo JSON declarativo que consume el runtime; no modifica Unity ni ejecuta código dentro del mod.

> Estado de integración: esta página documenta la actualización del editor visual. El comando solo estará disponible en una rama o distribución que incluya `jumpfall_menu_editor.py` y la entrada correspondiente en `pyproject.toml`.

## Requisitos

- Python 3.10 o posterior.
- Tk 8.6 / Tkinter.
- Windows, macOS o Linux.

En Debian/Ubuntu:

```bash
sudo apt install python3-tk
```

## Ejecutar

Desde `Tools/jumpfall-sdk`:

```bash
python3 jumpfall_menu_editor.py
```

Abrir proyecto al iniciar:

```bash
python3 jumpfall_menu_editor.py ruta/al/mod
```

Abrir un menú concreto:

```bash
python3 jumpfall_menu_editor.py ruta/al/mod/content/menus/main-menu.json
```

Si instalaste el proyecto con pip:

```bash
jumpfall-menu-editor
```

## Funciones

- Crear un proyecto mínimo con `jumpfall.mod.json`.
- Abrir un proyecto existente.
- Abrir un archivo de menú.
- Lienzo visual `1920×1080`.
- Agregar `panel`, `image`, `text` y `button`.
- Arrastrar elementos.
- Redimensionar desde el controlador inferior derecho.
- Editar ID, padre, texto, color, posición, tamaño, fuente, acción, target y value.
- Importar PNG/JPG/JPEG a `assets/images/`.
- Duplicar, borrar y reordenar capas.
- Guardar JSON.
- Registrar automáticamente el archivo en `content.menus`.
- Validar con `jumpfall_sdk.Validator`.
- Compilar con `jumpfall_sdk.pack_command`.

## Flujo de trabajo

1. **Archivo → Crear proyecto**.
2. Elige carpeta, ID, nombre y autor.
3. Agrega un panel.
4. Agrega textos, imágenes y botones.
5. Arrastra y redimensiona.
6. Configura la superficie `main` o `pause`.
7. Especifica la escena, normalmente `Menugame` o `*`.
8. Configura las acciones.
9. Guarda.
10. Valida.
11. Compila `.jfmod`.

## Acciones disponibles

El editor limita la lista a lo soportado por el runtime:

```text

resume
quit
load_map
set_active
toggle_active
```

No genera llamadas C#, `load_scene` ni acciones arbitrarias.

## Padres y orden

Un hijo usa coordenadas relativas al padre. El JSON debe declarar primero el padre:

```json
[
  { "id": "panel", "parent": "", "type": "panel" },
  { "id": "title", "parent": "panel", "type": "text" }
]
```

El editor intenta corregir el orden automáticamente, pero sigue siendo recomendable revisar el JSON antes de publicar.

## Imágenes

El importador copia archivos a:

```text
assets/images/
```

Tkinter suele mostrar preview directo de PNG. Un JPG puede aparecer como marcador en el editor, pero se guarda correctamente y JumpFall puede cargarlo.

## Prueba automática

```bash
python3 jumpfall_menu_editor.py --self-test
```

Comprueba:

- creación de proyecto;
- lectura y escritura del layout;
- registro en el manifiesto;
- normalización de colores;
- ejecución sin abrir la ventana.

## Limitaciones de esta versión

- Edita principalmente el primer layout del archivo.
- No renderiza una captura real de `Menugame` detrás del lienzo.
- No descubre automáticamente rutas de jerarquía de una build.
- `load_map` requiere que el mapa ya exista en el manifiesto.
- No corrige la falta de navegación con mando del runtime IMGUI.
- No crea armas, pickups ni lógica nueva.

## Próximas herramientas posibles

La misma base puede convertirse en editores visuales de:

- campañas;
- listas de mapas;
- HUD;
- objetos configurables;
- pickups;
- armas declarativas;
- diálogos y objetivos.
