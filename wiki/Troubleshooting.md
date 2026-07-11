# Solución de problemas

## El mod no aparece

- Confirma extensión `.jfmod`.
- Confirma `jumpfall.mod.json` en la raíz.
- Copia a `Documentos/jumpfall/mods/packages`.
- Vuelve a la escena `Menugame`, presiona `F10` y **Actualizar lista**.
- Ejecuta el validador.

## No se puede activar

Busca diagnósticos:

- `manifest.*`: manifiesto inválido.
- `resolve.dependency_missing`: dependencia obligatoria ausente.
- `resolve.dependency_cycle`: ciclo.
- `resolve.conflict`: conflicto declarado.
- `resolve.total_conversion`: segunda conversión completa.
- `lua.unavailable`: el paquete declara Lua.
- `package.security`: archivo o ruta bloqueada.

## **Reiniciar y aplicar** está deshabilitado

El perfil pendiente no superó la validación completa. El panel muestra el motivo y, para conflictos declarados, los nombres de ambos mods.

Casos habituales:

- dos mods se declaran incompatibles;
- hay más de una `total_conversion`;
- falta una dependencia obligatoria;
- existe un ciclo de dependencias;
- un mod seleccionado fue eliminado o actualizado a una versión incompatible.

Desactiva uno de los mods señalados y vuelve a comprobar el panel. El botón solo se habilita cuando el conjunto pendiente es válido.

`RestartGame()` repite la misma validación, por lo que no se puede evitar el bloqueo llamando al reinicio desde otra interfaz.

## El juego fue cerrado o reiniciado con conflictos pendientes

En el próximo inicio JumpFall:

1. rechaza el perfil pendiente inválido;
2. elimina ambos lados de cada conflicto;
3. elimina también mods que dependían obligatoriamente de los retirados;
4. valida estrictamente el resultado;
5. guarda el subconjunto seguro como perfil activo;
6. registra `profile.pending_auto_disable` en el diagnóstico.

Los paquetes `.jfmod` no se borran. Solo se desactivan dentro de `mod-profile.json`.

## Se activa, pero no cambia nada

- Debes reiniciar.
- Revisa `scene`.
- Revisa mayúsculas y rutas.
- Los selectores comienzan con `/`.
- Declara la capacidad correcta.
- Revisa `Player.log`.

## `scene_patch.target_missing`

La jerarquía no coincide. Los selectores son exactos y no usan búsqueda global.

## `menu.load_map`

- El target no coincide con un ID de `content.maps`.
- El `.jfue` falta.
- Ya hay otra carga en curso.
- `templateScene` no es `MapJfue`.

## El mapa carga roto

Un JSON válido no garantiza geometría correcta. Causas:

- `.jfue` escrito manualmente;
- escalas asumidas como `1×1`;
- spawn dentro de collider;
- fondo dibujado que no coincide con triggers;
- IDs no registrados;
- assets movidos después de compilar.

Solución: abre o reconstruye el mapa en Level Editor, prueba con `F5` y compila con `F8`.

## Fondo ausente

- PNG no está en `assetlocal/backgroundimg`.
- `fileName` contiene una ruta en vez de nombre.
- Capitalización incorrecta en Linux.
- El paquete no conservó la estructura.

## Audio ausente

- Solo WAV/OGG.
- Archivo no está en `assetlocal/sound` o ruta declarada.
- Volumen `0`.
- Archivo excede límites.

## Menú mal posicionado

- El sistema usa referencia 1920×1080.
- Revisa `x`, `y`, ancho y alto.
- Un hijo es relativo al padre.
- Usa el editor visual.

## Botones del mod no funcionan con mando

Limitación actual: los menús IMGUI de mods están orientados a mouse. El Input System del juego no transforma automáticamente esos botones en navegación de mando.

## La skin no aparece

- `.jvsk` en `skin/local`.
- `skin.json` en raíz.
- Estado Idle válido.
- Carpetas declaradas existen.
- Frames PNG no exceden límites.

## Frames fuera de orden

Usa:

```text
000.png
001.png
002.png
010.png
```

## El juego falla al iniciar

Arranca con:

```text
-safe_mode
```

Después vuelve a `Menugame`, abre F10, revisa diagnósticos y desactiva el último mod.

## Reportar un bug

Incluye:

- JumpFall y SDK version;
- sistema operativo;
- ID y versión del mod;
- pasos exactos;
- diagnóstico;
- fragmento relevante de Player.log;
- paquete mínimo reproducible sin credenciales ni datos personales.
