# Seguridad y límites

JumpFall Modding 1.0 acepta datos, no código arbitrario.

## Bloqueado

- DLL, EXE, SO y DYLIB.
- C# externo.
- Código nativo.
- AssetBundles externos.
- Scripts de sistema.
- Rutas absolutas.
- `..` y escapes de carpeta.
- Enlaces simbólicos dentro del paquete.
- Más de una conversión completa.
- Lua en `.jfmod`.
- Archivos `.lua`, incluso sin declarar.
- Red, procesos, reflexión y acceso libre al filesystem.

## Extensiones permitidas en `.jfmod`

```text
.json
.png
.jpg
.jpeg
.wav
.ogg
.jfue
.txt
.md
.csv
```

## Extensiones bloqueadas

```text
.dll .exe .so .dylib .bundle .assetbundle .cs .js
.bat .cmd .ps1 .sh .app .apk .jar .class .py .rb .com .scr
```

El `.py` del SDK vive fuera del paquete. No metas el editor o el compilador dentro de un `.jfmod`.

Las piezas añadidas al Level Editor tampoco cargan prefabs externos. Solo heredan
un arquetipo 2D permitido y aplican sprite, color y escala declarativos. El ID se
prefija con el ID del mod para que un paquete no suplante piezas de otro.

## Límites principales

| Recurso | Máximo |
| --- | --- |
| `.jfmod` comprimido | 256 MiB |
| contenido extraído | 512 MiB |
| archivo individual | 128 MiB |
| manifiesto | 256 KiB |
| imagen | 32 MiB y 4096×4096 |
| audio | 64 MiB |
| mapa `.jfue` | 16 MiB |
| archivos por paquete | 2000 |
| ratio sospechoso | 200:1 para archivos grandes |

Un `.jfue` de mod admite hasta 10000 piezas, 2000 triggers, 256 fondos y 256
pistas. El runtime recrea su caché antes de cargar y fuerza `lua.enabled=false`
en la copia temporal.

## Selectores protegidos

Los parches, `hideTargets`, `set_active` y `toggle_active` usan rutas exactas. Se
rechaza cualquier segmento relacionado con:

```text
player rigidbody collider camera spawn loading
modruntime modmanager eventsystem inputsystem
```

La comparación ignora espacios, guiones, guiones bajos y mayúsculas. Esto impide
que un mod declarativo desactive el jugador, la cámara, los colliders o los
sistemas que cargan y administran mods.

## Archivos ignorados

```text
.DS_Store
Thumbs.db
desktop.ini
__MACOSX/
```

## Extracción segura

Los sistemas de `.jfmod`, `.jsm` y `.jvsk` deben:

- extraer a staging;
- validar rutas antes de escribir;
- impedir ZIP Slip;
- limitar archivos y tamaño total;
- no seguir enlaces;
- mover al destino solo después de completar;
- mantener la instalación base intacta.

## Perfil transaccional

`mod-profile.json` mantiene:

- `active`: conjunto aplicado;
- `pending`: conjunto solicitado.

Si el conjunto pendiente falla, el runtime conserva el último estado seguro en lugar de ejecutar la mitad de los mods.

## Modo seguro

```text
-safe_mode
-no_mods
-disable_mods
```

No borra paquetes ni perfil; solamente omite la ejecución durante ese inicio.

## Cargadores externos

BepInEx, MelonLoader, Harmony, UnityExplorer y equivalentes no forman parte del sistema oficial. Un mod que dependa de ellos no es un `.jfmod` compatible y queda fuera de estas garantías.
