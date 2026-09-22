# Compatibilidad y pruebas

## Matriz de plataforma

| Función | Windows | macOS | Linux | Android/iOS |
| --- | --- | --- | --- | --- |
| Descubrir `.jfmod` | Sí | Sí | Sí | No |
| Gestor `F10` | Sí | Sí | Sí | No |
| Mapas `.jfue` en mod | Sí | Sí | Sí | No para `.jfmod` |
| Piezas de mod en Level Editor | Sí | Sí | Sí | No |
| Menús IMGUI | Sí | Sí | Sí | No para `.jfmod` |
| Skins `.jvsk` personales | Sí | Sí | Sí | No |
| SDK Python | Sí | Sí | Sí | No aplica |
| Editor visual Tkinter | Sí | Sí | Sí | No aplica |

## macOS

- Ruta típica: `~/Documents/jumpfall`.
- Algunos teclados requieren `Fn + F10`.
- Prueba permisos de Documentos/iCloud.
- El relanzamiento automático de una `.app` requiere prueba específica.
- Apple Silicon funciona con una build compatible; una build Universal amplía cobertura.

Log típico de Unity:

```text
~/Library/Logs/<Company Name>/<Product Name>/Player.log
```

## Linux

- El filesystem diferencia mayúsculas/minúsculas.
- Usa nombres en minúsculas y `/`.
- `Background.png` y `background.png` son archivos distintos.
- Prueba permisos de `~/Documents` o el fallback persistente.

## Windows

- Documentos puede estar redirigido por OneDrive.
- No uses rutas absolutas dentro del mod.
- Prueba con nombres de usuario que contengan espacios o caracteres no ASCII.

## Checklist mínimo de `.jfmod`

1. El juego inicia sin mods.
2. `F10` abre el gestor.
3. El paquete aparece.
4. La validación no muestra errores.
5. Activar guarda estado pendiente.
6. Reiniciar aplica.
7. El contenido aparece.
8. Desactivar y reiniciar restaura el juego.
9. `-safe_mode` inicia sin ejecutar el mod.
10. No se modificó la instalación base.

## Checklist de mapas

- Guardado `.jmap` con `F7`.
- Playtest `F5`.
- Compilación `.jfue` con `F8`.
- Spawn fuera de colliders.
- Suelos y triggers alineados.
- Fondo no tapa al jugador.
- Audio carga y respeta volumen.
- Gravedad guardada.
- `finish_level` vuelve a `Menugame`.
- Assets conservan `assetlocal`.

## Checklist de skins

- `skin.json` en raíz.
- Frames PNG.
- Nombres con ceros a la izquierda.
- Pivot correcto.
- Idle existe.
- Estados faltantes tienen fallback razonable.
- Preview y meta opcionales válidos.
- Activar/desactivar restaura el player base.

## Checklist del editor visual

Después de integrar la actualización que contiene `jumpfall_menu_editor.py`:

```bash
python3 -m py_compile Tools/jumpfall-sdk/jumpfall_menu_editor.py
python3 Tools/jumpfall-sdk/jumpfall_menu_editor.py --self-test
```

Después prueba manualmente:

- crear proyecto;
- mover y redimensionar;
- importar PNG;
- guardar;
- reabrir;
- validar;
- compilar;
- instalar el `.jfmod` resultante.

## Unity

Antes de una release pública:

- abrir con Unity `6000.3.8f1`;
- esperar recompilación completa;
- confirmar cero errores;
- probar Play Mode;
- compilar Windows, macOS y Linux;
- confirmar que Android/iOS no inicializan `.jfmod` ni skins personales.
