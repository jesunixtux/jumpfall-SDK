# JumpFall Visual Menu Editor

Editor visual de menús para `jumpfall-sdk` y el runtime Modding 1.0 de JumpFall.

## Estado

Primera versión funcional del editor. Genera el mismo JSON declarativo que usa
JumpFall; no modifica el juego base ni ejecuta código dentro del mod.

Funciones incluidas:

- crear un proyecto mínimo de mod;
- abrir una carpeta que contenga `jumpfall.mod.json`;
- abrir un archivo de menú existente;
- lienzo visual de referencia `1920x1080`;
- agregar `panel`, `image`, `text` y `button`;
- mover elementos con el mouse;
- cambiar tamaño con el controlador inferior derecho;
- editar ID, padre, texto, color, posición, tamaño, fuente, acción y target;
- importar imágenes PNG/JPG/JPEG al proyecto;
- duplicar, eliminar y reordenar capas;
- guardar el JSON;
- registrar automáticamente el menú en el manifiesto;
- validar usando `jumpfall_sdk.Validator`;
- empaquetar usando `jumpfall_sdk.pack_command`;
- atajos de teclado para guardar, duplicar, eliminar y mover.

## Requisitos

- Python 3.10 o posterior;
- Tk 8.6 / Tkinter;
- Windows, macOS o Linux.

En las distribuciones oficiales de Python para Windows y macOS, Tkinter suele
venir incluido. En Debian/Ubuntu puede instalarse con el paquete `python3-tk`.

## Ejecutar directamente

Desde `Tools/jumpfall-sdk`:

```bash
python3 jumpfall_menu_editor.py
```

Abrir un proyecto o menú al iniciar:

```bash
python3 jumpfall_menu_editor.py ruta/al/mod
python3 jumpfall_menu_editor.py ruta/al/mod/content/menus/main-menu.json
```

## Instalar comandos del SDK

Desde la carpeta del SDK:

```bash
python3 -m pip install .
```

Después estarán disponibles:

```bash
jumpfall-sdk validate ruta/al/mod
jumpfall-sdk pack ruta/al/mod
jumpfall-menu-editor
```

## Flujo recomendado

1. Abre `jumpfall-menu-editor`.
2. Selecciona **Archivo → Crear proyecto**.
3. Elige el ID, nombre y autor.
4. Agrega paneles, textos, imágenes y botones.
5. Arrastra los elementos en el lienzo.
6. Configura las acciones del botón.
7. Guarda.
8. Pulsa **Validar**.
9. Pulsa **Compilar .jfmod**.
10. Copia el resultado a `Documentos/jumpfall/mods/packages`.

## Acciones disponibles

El editor limita la lista a las acciones que reconoce el runtime actual:

- vacío;
- `resume`;
- `quit`;
- `load_map`;
- `set_active`;
- `toggle_active`.

No crea `load_scene`, llamadas C# ni acciones arbitrarias.

## Coordenadas y padres

El lienzo usa el mismo sistema del runtime:

- resolución de referencia: `1920x1080`;
- `x = 0`, `y = 0`: centro de la pantalla;
- `y` positivo: hacia arriba;
- los hijos se posicionan con relación al centro de su padre;
- el padre debe aparecer antes que sus hijos en el JSON.

El editor corrige el orden de padres e hijos cuando es posible.

## Imágenes

El botón de importar copia la imagen a:

```text
assets/images/
```

El preview directo se muestra para PNG cuando Tk puede decodificarlo. Los JPG y
JPEG se representan como un marcador visual, pero se guardan correctamente y el
runtime de JumpFall puede cargarlos.

## Prueba automática

```bash
python3 jumpfall_menu_editor.py --self-test
```

La prueba comprueba creación de proyecto, lectura/escritura del layout, registro
en el manifiesto y normalización de colores. No abre una ventana.

## Limitaciones actuales

- edita el primer layout del archivo de menú;
- no muestra una captura real de la escena `Menugame` detrás del lienzo;
- no conoce automáticamente las rutas de jerarquía de una build;
- `load_map` requiere que el mapa ya esté declarado en el manifiesto;
- la navegación de mando sigue siendo una limitación del runtime, no del editor;
- el editor no agrega todavía armas, objetos ni lógica nueva.

## Siguiente etapa sugerida

Después de validar este editor, el mismo enfoque puede reutilizarse para crear
editores visuales de:

- campañas y listas de mapas;
- objetos configurables;
- pickups y modificadores;
- armas declarativas;
- HUD y menús de pausa.
