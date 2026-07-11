# Ejemplos completos

## 1. Mod de movilidad

```json
{
  "schemaVersion": "1.0.0",
  "id": "com.ejemplo.momentum",
  "name": "Momentum",
  "version": "1.0.0",
  "author": "Ejemplo",
  "description": "Movilidad alternativa.",
  "type": "content",
  "gameVersion": { "min": "0.50.05", "max": "" },
  "priority": 100,
  "dependencies": [],
  "conflicts": [],
  "capabilities": ["mechanics"],
  "content": {
    "maps": [],
    "scenePatches": [],
    "menus": [],
    "localization": [],
    "scripts": [],
    "playerTuning": {
      "moveSpeedMultiplier": 1.15,
      "jumpForceMultiplier": 1.10,
      "gravityMultiplier": 0.85,
      "dashSpeedMultiplier": 1.20,
      "maxJumpsDelta": 1
    }
  }
}
```

## 2. Menú con botón de mapa

Manifiesto:

```json
"capabilities": ["maps", "menus"],
"content": {
  "maps": [
    {
      "id": "prueba",
      "name": "Mapa de prueba",
      "file": "content/maps/prueba.jfue",
      "templateScene": "MapJfue"
    }
  ],
  "menus": ["content/menus/main.json"]
}
```

Menú:

```json
{
  "menus": [
    {
      "id": "selector",
      "surface": "main",
      "scene": "Menugame",
      "hideTargets": [],
      "sortingOrder": 500,
      "elements": [
        {
          "id": "panel",
          "parent": "",
          "type": "panel",
          "text": "",
          "localizationKey": "",
          "asset": "",
          "color": "#101820EE",
          "x": 500,
          "y": 0,
          "width": 600,
          "height": 500,
          "fontSize": 24,
          "action": "",
          "target": "",
          "value": ""
        },
        {
          "id": "play",
          "parent": "panel",
          "type": "button",
          "text": "Jugar mapa",
          "localizationKey": "",
          "asset": "",
          "color": "#FFFFFFFF",
          "x": 0,
          "y": 0,
          "width": 360,
          "height": 72,
          "fontSize": 28,
          "action": "load_map",
          "target": "prueba",
          "value": ""
        }
      ]
    }
  ]
}
```

## 3. Localización

Manifiesto:

```json
"localization": [
  {
    "language": "SpanishLatam",
    "file": "content/localization/es-419.json"
  }
]
```

Archivo:

```json
{
  "items": [
    {
      "key": "com.ejemplo.mod.title",
      "value": "Mi campaña"
    }
  ]
}
```

## 4. Parche de texto

```json
{
  "patches": [
    {
      "scene": "Menugame",
      "target": "/Canvas/MainPanel/Title",
      "operation": "set_text",
      "value": "JumpFall personalizado",
      "asset": "",
      "localizationKey": "",
      "boolValue": true,
      "numberValue": 1.0
    }
  ]
}
```

La ruta es un ejemplo. Debe coincidir con la jerarquía real de tu build.

## 5. Skin mínima

```text
mi-skin.jvsk
├── skin.json
└── idle/
    ├── 000.png
    └── 001.png
```

```json
{
  "active": false,
  "fps": 10,
  "visual": {
    "scale": 1.0,
    "widthScale": 1.0,
    "heightScale": 1.0,
    "mirror": true,
    "colorOverlay": [255, 255, 255, 255]
  },
  "files": {
    "idle": {
      "path": "idle",
      "fps": 10,
      "pivotX": 0.5,
      "pivotY": 0.0,
      "xOffset": 0.0,
      "yOffset": 0.0,
      "loop": true
    }
  }
}
```

## 6. Empaquetar manualmente

Un `.jfmod` es ZIP, pero usa el SDK para evitar raíces incorrectas:

```bash
python3 jumpfall_sdk.py pack mi-mod -o mi-mod.jfmod
```

Una `.jvsk` puede crearse comprimiendo `skin.json` y carpetas directamente en la raíz y cambiando la extensión del ZIP a `.jvsk`.
