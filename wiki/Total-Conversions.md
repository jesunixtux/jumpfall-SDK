# Conversiones completas

Una conversión completa declara:

```json
"type": "total_conversion"
```

Solo puede haber una activa.

## Qué puede cambiar

- Menú principal.
- Menú de pausa.
- Campaña de mapas `.jfue`.
- Fondos, imágenes, sprites y colores.
- Música y efectos.
- Textos y localización.
- HUD declarativo.
- Velocidad, salto, gravedad, dash y saltos máximos dentro de límites.

## Qué conserva

- Ejecutable base.
- Escenas permitidas como plantillas.
- `PlayerMovement`.
- Física y gameplay 2D.
- Validación de paquetes.
- Modo seguro.

## Qué no puede hacer

- Distribuir JumpFall dentro del mod.
- Sobrescribir archivos instalados.
- Ejecutar C#, DLL o código nativo.
- Usar BepInEx, MelonLoader, Harmony o inyectores como parte del formato oficial.
- Sustituir el controlador del jugador.
- Crear movimiento principal en un entorno 3D.
- Acceder libremente a red, procesos, Steam o credenciales.
- Activar Lua en `.jfmod`.

## Campaña recomendada

Una campaña puede declarar varios mapas:

```json
"maps": [
  {
    "id": "capitulo-1",
    "name": "Capítulo 1",
    "file": "content/maps/capitulo-1.jfue",
    "templateScene": "MapJfue"
  },
  {
    "id": "capitulo-2",
    "name": "Capítulo 2",
    "file": "content/maps/capitulo-2.jfue",
    "templateScene": "MapJfue"
  }
]
```

El menú puede usar botones `load_map`. Dentro de un `.jfue`, `changelevel` puede apuntar a otro mapa compilado por nombre.

## Conversión basada en campaña original

También puedes dejar `maps` vacío y modificar la campaña base solo mediante `playerTuning`, menús y parches. En ese caso el botón New Game original sigue cargando las escenas originales.

## Ejemplo de movimiento alternativo

```json
"playerTuning": {
  "moveSpeedMultiplier": 1.15,
  "jumpForceMultiplier": 1.10,
  "gravityMultiplier": 0.85,
  "dashSpeedMultiplier": 1.20,
  "maxJumpsDelta": 1
}
```

La mayor movilidad puede permitir saltarse secciones de mapas. Eso debe considerarse parte del diseño o probarse antes de publicar.

## Compatibilidad con mods de contenido

Un mod de contenido puede acompañar a la conversión si:

- no declara conflicto;
- sus dependencias se resuelven;
- no intenta activar otra conversión;
- no pisa el mismo menú de forma incompatible.

## Diseño seguro

- Mantén un botón de salir.
- Conserva fallback al menú base durante desarrollo.
- Prueba activar y desactivar.
- Prueba modo seguro.
- Usa mapas exportados por el Level Editor.
- Declara conflictos explícitos con otras conversiones conocidas.
