# Instalación y primer mod

## Requisitos

- JumpFall instalado en Windows, macOS o Linux.
- Python 3.10 o superior.
- El contenido de `Tools/jumpfall-sdk` o la repo independiente `jumpfall-SDK`.
- Un editor de texto. Visual Studio Code es opcional.
- Tkinter solo es necesario para el editor visual de menús.

## Carpetas del jugador

JumpFall utiliza la carpeta Documentos del usuario:

```text
Documentos/
└── jumpfall/
    ├── mods/
    │   ├── packages/
    │   └── mod-profile.json
    ├── levels/
    │   ├── creations/
    │   ├── compilator/
    │   ├── assetslocal/
    │   └── workshop/
    └── skin/
        ├── local/
        ├── workshop/
        └── temp_extract/
```

En macOS, `Documentos` normalmente corresponde a:

```text
~/Documents
```

Si el sistema no puede resolver Documentos, algunos subsistemas usan `Application.persistentDataPath` como fallback.

## Instalar el SDK como comandos

Desde `Tools/jumpfall-sdk`:

```bash
python3 -m pip install .
```

Comandos resultantes:

```bash
jumpfall-sdk --version
jumpfall-sdk validate ruta/al/mod
jumpfall-sdk pack ruta/al/mod
jumpfall-menu-editor
```

También puedes ejecutar los scripts sin instalar:

```bash
python3 jumpfall_sdk.py validate ruta/al/mod
python3 jumpfall_sdk.py pack ruta/al/mod
python3 jumpfall_menu_editor.py
```

## Crear el proyecto mínimo

Copia la plantilla:

```bash
cp -R templates/content-mod mi-primer-mod
```

En PowerShell:

```powershell
Copy-Item -Recurse templates/content-mod mi-primer-mod
```

Estructura mínima:

```text
mi-primer-mod/
├── jumpfall.mod.json
├── content/
├── assets/
└── README.md
```

El manifiesto debe estar directamente en la raíz. Esto es incorrecto:

```text
mi-primer-mod.jfmod/
└── mi-primer-mod/
    └── jumpfall.mod.json
```

## Cambios obligatorios

Edita al menos:

```json
{
  "id": "com.tuusuario.mi-primer-mod",
  "name": "Mi primer mod",
  "version": "1.0.0",
  "author": "Tu nombre",
  "description": "Mi primera prueba de JumpFall Modding 1.0"
}
```

El `id` debe permanecer estable en futuras actualizaciones.

## Validar

```bash
python3 jumpfall_sdk.py validate mi-primer-mod
```

Salida esperada:

```text
[OK] Valid JumpFall mod for SDK 1.0.0.
```

## Empaquetar

```bash
python3 jumpfall_sdk.py pack mi-primer-mod
```

Salida personalizada:

```bash
python3 jumpfall_sdk.py pack mi-primer-mod -o dist/mi-primer-mod.jfmod
```

`pack` ejecuta la validación primero. Si existe un error, no crea el paquete.

## Instalar en JumpFall

Copia el resultado a:

```text
Documentos/jumpfall/mods/packages/
```

Después:

1. Abre JumpFall y permanece en la escena principal `Menugame`.
2. Presiona `F10` o `Fn + F10` en algunos teclados de macOS.
3. Pulsa **Actualizar lista**.
4. Selecciona el mod.
5. Actívalo.
6. Pulsa **Reiniciar y aplicar**.

El gestor solo puede abrirse dentro de `Menugame`. En niveles, Level Editor y otras escenas, `F10` queda disponible para las funciones propias de esas escenas.

Activar y desactivar usa un perfil pendiente. El cambio no se aplica parcialmente durante la sesión actual.

Antes de reiniciar, JumpFall vuelve a validar el perfil completo. Cuando detecta conflictos, dependencias ausentes, ciclos o más de una conversión completa:

- muestra los mods implicados;
- recomienda desactivar uno de los mods incompatibles;
- deshabilita **Reiniciar y aplicar**;
- bloquea también cualquier llamada directa al reinicio del runtime.

Si el proceso se cierra o reinicia externamente con un perfil pendiente inválido, el siguiente inicio construye un subconjunto seguro, desactiva los mods conflictivos y sus dependientes afectados, y guarda el perfil recuperado.

## Modo seguro

Argumentos:

```text
-safe_mode
-no_mods
-disable_mods
```

El modo seguro conserva los paquetes y el perfil, pero no ejecuta mods en ese inicio.
