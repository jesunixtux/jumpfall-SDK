# Changelog

Todos los cambios relevantes del SDK se documentan aquí. El proyecto sigue
[Semantic Versioning](https://semver.org/).

## Sin publicar

- Bloqueo de salidas `.jfmod` dentro de la carpeta fuente.
- Reglas de selectores críticos alineadas con el runtime.
- Rechazo incondicional de archivos Lua en paquetes `.jfmod`.
- Límites de tamaño y cantidad para mapas, piezas, triggers, fondos y pistas.
- Limpieza del caché de mapas y restauración completa del estado de pausa.
- `pack` ahora muestra advertencias válidas antes de crear el archivo.
- Wiki de mapas actualizada a `LevelData` v29 con timers, eventos seguros,
  ghost-player y conversión oficial `JMAP -> .unity`.
- Ghost-player enlazado a la raíz visual del player instanciado y a la JVSK
  activa de PC, con fallback a la skin base y sin incrustar skins en el mapa.

## 1.0.0 - 2026-07-11

- Contrato inicial de paquetes `.jfmod` y manifiesto `jumpfall.mod.json` 1.0.0.
- CLI Python sin dependencias para validar y empaquetar mods.
- Editor visual declarativo de menús.
- Schemas, plantilla, pruebas automáticas y wiki en español.
- Registro seguro de piezas 2D de mods en el Level Editor de PC.
- Validación de arquetipos e IDs de piezas dentro de mapas `.jfue`.


### Iluminación dinámica, extensión opcional de mapas v29

- Validación de `lights`, `id: light` y `set_light` con on/off/toggle.
- Límite de 256 luces por mod, valores finitos, IDs y vértices comprobados.
- Esquema de mapas y build reports actualizado; ejemplo `examples/lighting.jfue`.
- Sin cambio de versión del mapa o del manifiesto.
