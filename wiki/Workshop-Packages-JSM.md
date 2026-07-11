# Paquetes Workshop `.jsm`

`.jsm` es el formato histórico de paquetes de mapas de Steam Workshop. Internamente es un ZIP UTF-8 con extensión propia.

## Relación de formatos

```text
.jmap  -> fuente editable
.jfue  -> mapa jugable
.jsm   -> paquete Workshop del mapa
.jfmod -> mod general, puede incluir varios .jfue
```

## Estructura mínima

```text
mi_mapa.jfue
manifest.json
```

Con assets:

```text
mi_mapa.jfue
manifest.json
assetlocal/
├── backgroundimg/
│   └── background.png
├── sound/
│   └── tema.ogg
└── lua/
    └── main.lua
```

La carpeta moderna es `assetlocal`. `assetslocal` se acepta solo por compatibilidad.

## `manifest.json`

```json
{
  "formatVersion": 1,
  "packageType": "jumpfall_map",
  "mapFile": "mi_mapa.jfue",
  "workshopId": "1234567890",
  "createdUtc": "2026-07-11T00:00:00Z"
}
```

Campos:

- `formatVersion`: actualmente `1`.
- `packageType`: `jumpfall_map`.
- `mapFile`: nombre interno del `.jfue`.
- `workshopId`: ID de Steam o `local_test`.
- `createdUtc`: ISO 8601 UTC.

## Crear desde el Level Editor

1. Presiona `F8`.
2. Escribe el nombre del mapa.
3. Escribe el Workshop ID o `local_test`.
4. Pulsa **Compile + .jsm** si la build habilita esa función.

La documentación del proyecto también contempla un compilador JSM externo porque la creación en runtime puede estar deshabilitada en builds públicas.

## Instalación

El juego extrae en:

```text
Documentos/jumpfall/levels/workshop/{workshopId}/
```

Resultado típico:

```text
1234567890/
├── mi_mapa.jfue
├── mi_mapa.jsm
└── assetlocal/
```

## Seguridad

La instalación debe:

- rechazar rutas ZIP Slip;
- aceptar solo extensiones permitidas;
- exigir al menos un `.jfue`;
- extraer dentro de la carpeta del Workshop ID;
- no ejecutar archivos del paquete.

## Diferencias con `.jfmod`

`.jsm`:

- representa principalmente un mapa;
- sigue el flujo de Steam Workshop de mapas;
- contiene su propio `manifest.json`.

`.jfmod`:

- puede agrupar mapas, menús, audio, visuales, localización y mecánicas limitadas;
- usa `jumpfall.mod.json`;
- requiere activación y reinicio;
- puede ser una conversión completa.

No cambies solo la extensión de un `.jsm`. Migra el `.jfue`, assets y metadatos a una plantilla `.jfmod`.
