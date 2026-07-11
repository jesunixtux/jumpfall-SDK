# Piezas de mods en el Level Editor

Los mods `.jfmod` activos pueden registrar piezas 2D propias en el Level Editor
de PC. La pieza aparece en la paleta, puede colocarse como una pieza normal y se
guarda en `.jmap` y `.jfue`. El juego base no se edita.

## Modelo de seguridad

Una pieza de mod no es un prefab externo. Es una definición JSON que hereda uno
de los prefabs 2D oficiales. El autor puede cambiar su presentación y escala,
pero no agregar componentes, ejecutar código ni sustituir el controlador.

Esto mantiene cuatro límites:

- solo arquetipos 2D incluidos por JumpFall;
- ningún DLL, C#, AssetBundle o prefab externo;
- ningún personaje que se mueva en un entorno 3D;
- ninguna mecánica libre fuera del comportamiento del arquetipo.

## 1. Declarar la capacidad

En `jumpfall.mod.json`:

```json
{
  "capabilities": ["level_editor"],
  "content": {
    "levelEditor": ["content/level-editor/pieces.json"]
  }
}
```

`levelEditor` puede contener varios archivos JSON. Los IDs de pieza deben ser
únicos dentro del mod.

## 2. Crear el catálogo

```json
{
  "pieces": [
    {
      "id": "blue-platform",
      "name": "Blue Platform",
      "baseId": "box_ground",
      "asset": "assets/images/blue-platform.png",
      "color": "#FFFFFFFF",
      "pixelsPerUnit": 100,
      "scaleX": 2,
      "scaleY": 1
    }
  ]
}
```

Campos:

| Campo | Obligatorio | Regla |
| --- | --- | --- |
| `id` | Sí | 1–64 caracteres: minúsculas, números, punto, guion o guion bajo. |
| `name` | Sí | Nombre visible, 1–128 caracteres. |
| `baseId` | Sí | Uno de los arquetipos permitidos. |
| `asset` | No | PNG, JPG o JPEG dentro del paquete. |
| `color` | No | `#RRGGBB` o `#RRGGBBAA`. |
| `pixelsPerUnit` | No | 1–1000; por defecto 100. |
| `scaleX`, `scaleY` | No | Ambos 0 para heredar o ambos entre 0.05 y 100. |

## 3. Elegir el arquetipo

| `baseId` | Qué hereda |
| --- | --- |
| `box_ground` | Plataforma y collider de suelo. |
| `checkpoint` | Punto de control. |
| `apple` | Coleccionable de manzana. |
| `orb_jump` | Orbe de salto. |
| `plane_jump` | Plataforma de impulso y sus parámetros del mapa. |
| `elevator` | Elevador 2D y sus parámetros del mapa. |

La imagen no altera el collider ni la lógica heredada. Comprueba visualmente la
escala y la colisión durante el playtest.

## 4. Identificador dentro del mapa

JumpFall convierte el ID local en:

```text
<id-del-mod>:<id-de-pieza>
```

Ejemplo:

```text
com.autor.castillo:blue-platform
```

El prefijo evita colisiones. No escribas otro prefijo manualmente: activa el mod
y deja que el Level Editor coloque y guarde la pieza.

## 5. Probar y compilar

1. Ejecuta `jumpfall-sdk validate`.
2. Empaqueta e instala el `.jfmod`.
3. Activa el mod desde el gestor y reinicia JumpFall.
4. Abre Level Editor desde el menú principal.
5. Busca el `name` de la pieza en la paleta.
6. Colócala, prueba el mapa y compila con `F8`.
7. Copia el `.jfue` a `content/maps/` y decláralo en `content.maps`.
8. Vuelve a validar y empaquetar.

El reinicio es obligatorio porque el catálogo activo se fija al arrancar. Esta
función no existe en Android ni iOS.

## 6. Dependencias y distribución

El mapa requiere el mod que posee la pieza. Lo más sencillo es distribuir mapa y
catálogo en el mismo `.jfmod`. Si otro mod registra el mapa, debe declarar una
dependencia obligatoria hacia el mod que aporta las piezas.

Si la pieza no está disponible, el cargador la omite y registra un diagnóstico;
no sustituye silenciosamente el ID con una pieza diferente.

## Límites actuales

- máximo 128 piezas por archivo de catálogo;
- sprites de hasta 32 MiB y 4096×4096 al decodificar;
- no hay triggers personalizados en este contrato;
- no hay prefabs o componentes personalizados;
- no hay scripts Lua en `.jfmod`;
- la mecánica siempre procede del `baseId` permitido.

Usa los triggers oficiales para muerte, final, cambio de mapa, cámara, visibilidad
y eventos. Para proponer un arquetipo nuevo, primero debe implementarse y probarse
en el juego base, y luego añadirse al runtime, SDK, schema, plantilla y wiki.
