# Crear un mod

Esta página describe el flujo recomendado para desarrollar un `.jfmod` sin mezclar demasiados sistemas al principio.

## 1. Decide el tipo

### `content`

Úsalo para contenido compatible con el juego o con otras conversiones:

- un mapa;
- una traducción;
- un tema visual;
- música;
- un HUD;
- ajustes moderados de movimiento.

### `total_conversion`

Úsalo cuando el paquete pretenda reemplazar la presentación, campaña o recorrido principal. Solo puede existir una conversión completa activa.

## 2. Usa un ID estable

Formato válido:

```text
com.autor.nombre-mod
```

Reglas:

- entre 3 y 64 caracteres;
- minúsculas, números, punto, guion y guion bajo;
- debe comenzar con letra minúscula o número;
- no puede ser `jumpfall`;
- no lo cambies entre versiones.

## 3. Declara solamente las capacidades usadas

```json
"capabilities": [
  "visuals",
  "menus"
]
```

Capacidades disponibles:

```text
maps
visuals
audio
localization
menus
mechanics
```

`lua` no está disponible para `.jfmod`.

## 4. Organiza el proyecto

```text
mi-mod/
├── jumpfall.mod.json
├── content/
│   ├── maps/
│   ├── menus/
│   ├── patches/
│   └── localization/
├── assets/
│   ├── images/
│   └── audio/
└── README.md
```

No se descubren archivos automáticamente. Cada archivo que el runtime deba usar debe estar referenciado desde `content` o desde un JSON declarado.

## 5. Trabaja de pequeño a grande

Orden recomendado:

1. Cambia un texto o crea un panel simple.
2. Valida y prueba.
3. Añade imágenes.
4. Añade audio o localización.
5. Añade mapas compilados por el Level Editor.
6. Solo al final crea una conversión completa.

Esto evita que un error en veinte archivos parezca un fallo del cargador.

## 6. Menús

Puedes escribir el JSON manualmente o usar:

```bash
python3 jumpfall_menu_editor.py
```

El editor visual permite arrastrar, redimensionar, agregar y quitar elementos, y luego invoca el mismo validador y empaquetador del SDK.

## 7. Mapas

No construyas un `.jfue` a mano salvo que estés desarrollando una herramienta especializada que conozca la escala real de todos los prefabs.

Flujo correcto:

1. Abre Level Editor.
2. Crea el mapa con piezas registradas.
3. Prueba con `F5`.
4. Guarda editable con `F7`.
5. Compila jugable con `F8`.
6. Copia el `.jfue` y sus assets conservando la estructura.

## 8. Skins

Las skins `.jvsk` son un sistema separado de `.jfmod`. No renombres un `.jvsk` a `.jfmod`. Consulta [Skins `.jvsk`](Skins-JVSK).

## 9. Versiona el mod

Usa SemVer:

```text
1.0.0
1.1.0
2.0.0-beta.1
```

Incrementa:

- parche: correcciones compatibles;
- menor: funciones nuevas compatibles;
- mayor: cambios incompatibles.

## 10. Checklist de publicación

- El manifiesto valida.
- No hay archivos fuera de la allowlist.
- No hay rutas absolutas ni `..`.
- El mod inicia y se desactiva limpiamente.
- Se probó el sistema operativo declarado.
- Los mapas salieron del Level Editor.
- Las imágenes respetan 4096×4096 y 32 MiB.
- Los audios son WAV u OGG.
- La conversión completa conserva una forma de jugar o salir.
- El README explica instalación, versión, autor y compatibilidad.
