# JumpFall Modding Wiki

Bienvenido a la documentación técnica y de autoría para crear contenido externo de JumpFall.

Esta wiki cubre los cuatro sistemas de contenido que existen actualmente:

| Sistema | Extensión | Propósito |
| --- | --- | --- |
| Modding 1.0 | `.jfmod` | Paquete general para mapas, menús, visuales, audio, localización y ajustes limitados de jugabilidad. |
| Level Editor | `.jmap` / `.jfue` | Mapa editable y mapa compilado/jugable. |
| Workshop de mapas | `.jsm` | Paquete ZIP de un mapa `.jfue` junto con sus assets. |
| Skins visuales | `.jvsk` | Paquete de animaciones PNG para reemplazar visualmente al jugador. |

## Versiones documentadas

- Juego conocido por el runtime: `0.50.05`
- Schema `.jfmod`: `1.0.0`
- SDK: `1.0.0`
- Formato `LevelData`: versión `16`
- Unity del proyecto: `6000.3.8f1` — Unity 6.3

## Plataformas

| Plataforma | `.jfmod` | `.jvsk` personal | Level Editor / mapas |
| --- | --- | --- | --- |
| Windows Standalone | Sí | Sí | Sí |
| macOS Standalone | Sí | Sí | Sí |
| Linux Standalone | Sí | Sí | Sí |
| Unity Editor en PC | Desarrollo | Desarrollo | Desarrollo |
| Android | No | No | El juego puede contener herramientas móviles, pero no instala `.jfmod` ni skins personales. |
| iOS | No | No | El juego puede contener herramientas móviles, pero no instala `.jfmod` ni skins personales. |

## Qué puede hacer un `.jfmod`

- Registrar mapas `.jfue` compilados con el Level Editor.
- Agregar piezas 2D seguras del mod a la paleta del Level Editor en PC.
- Crear capas de menú principal o pausa mediante IMGUI.
- Cambiar texto, sprites, colores, audio y visibilidad de objetos de escenas permitidas.
- Añadir localización para `English` y `SpanishLatam`.
- Ajustar moderadamente velocidad, salto, gravedad, dash y cantidad de saltos.
- Crear una conversión completa que combine estos recursos.

## Qué no puede hacer todavía

- Ejecutar C#, DLL, código nativo o AssetBundles externos.
- Sustituir `PlayerMovement`.
- Crear una mecánica completamente nueva solo con JSON, como una pistola con código propio.
- Usar Lua dentro de `.jfmod`; el runtime lo rechaza con `lua.unavailable`.
- Cargar escenas internas arbitrarias con `load_scene`.
- Instalar mods en Android o iOS.

## Inicio rápido

1. Instala Python 3.10 o superior.
2. Abre `Tools/jumpfall-sdk`.
3. Copia la plantilla `templates/content-mod`.
4. Edita `jumpfall.mod.json`.
5. Valida:

```bash
python3 jumpfall_sdk.py validate ruta/al/mod
```

6. Empaqueta:

```bash
python3 jumpfall_sdk.py pack ruta/al/mod
```

7. Copia el `.jfmod` a:

```text
Documentos/jumpfall/mods/packages/
```

8. Abre JumpFall, presiona `F10`, actualiza, activa y usa **Reiniciar y aplicar**.

## Navegación

- [Arquitectura y mapa del código](Architecture-and-Source-Map)
- [Instalación y primer mod](Getting-Started)
- [Crear un mod](Creating-a-Mod)
- [Manifiesto 1.0](Manifest-1.0)
- [Capacidades y contenido](Capabilities-and-Content)
- [Menús y parches de escena](Menus-and-Scene-Patches)
- [Editor visual de menús](Visual-Menu-Editor)
- [Mapas y Level Editor](Maps-and-Level-Editor)
- [Piezas de mods en Level Editor](Custom-Level-Editor-Pieces)
- [Referencia del formato de mapas](Map-Format-Reference)
- [Paquetes Workshop `.jsm`](Workshop-Packages-JSM)
- [Skins `.jvsk`](Skins-JVSK)
- [Conversiones completas](Total-Conversions)
- [Ejemplos completos](Examples)
- [Compatibilidad y pruebas](Compatibility-and-Testing)
- [Seguridad y límites](Security-and-Limits)
- [Solución de problemas](Troubleshooting)
- [Extender JumpFall con objetos y armas](Extending-JumpFall)

## Estado honesto

El runtime y el SDK son funcionales en estado mínimo y ya se han probado paquetes reales en macOS. Aun así, cada mod debe validarse en una build compatible. Un JSON válido no garantiza que un mapa construido manualmente tenga escalas, colliders o prefabs correctos; para mapas jugables se debe usar el Level Editor y compilar con `F8`.
