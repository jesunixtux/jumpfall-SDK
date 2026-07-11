# Extender JumpFall con objetos, items y armas

El formato actual está diseñado para datos seguros. Para agregar una mecánica nueva —por ejemplo una pistola— primero debe existir un sistema genérico dentro del juego base.

## Por qué un `.jfmod` no puede crear una pistola hoy

Una pistola funcional necesita lógica para:

- apuntar con mouse o stick;
- disparar;
- crear o simular proyectiles;
- calcular daño;
- manejar munición;
- recargar;
- reproducir animaciones y audio;
- integrarse con Input System;
- limitar rendimiento y abuso.

Permitir C# externo resolvería esto, pero rompería el modelo de seguridad y compatibilidad.

## Arquitectura recomendada

JumpFall puede incluir componentes oficiales:

```text
JumpfallItemController
JumpfallItemDefinition
JumpfallWeaponController
JumpfallWeaponDefinition
JumpfallProjectile2D
JumpfallWeaponPickup
JumpfallInventory
```

Los mods solo declararían datos.

## Ejemplo futuro de arma

```json
{
  "id": "com.autor.weapon.pistol",
  "name": "Pistola básica",
  "mode": "mouse_aim",
  "damage": 20,
  "fireInterval": 0.3,
  "magazineSize": 8,
  "reloadSeconds": 1.4,
  "projectileSpeed": 22,
  "automatic": false,
  "sprite": "assets/weapons/pistol.png",
  "projectileSprite": "assets/weapons/bullet.png",
  "fireSound": "assets/audio/pistol.wav"
}
```

## Modos de item posibles

### Estático

El item apunta en la dirección del player o usa una orientación fija. Es simple y compatible con mando.

### Mouse aim

El arma rota hacia la posición del mouse. Requiere una acción oficial de apuntado y convertir correctamente coordenadas de pantalla a mundo.

### Stick aim

Usa el stick derecho. Debe compartir la misma interfaz de apuntado que mouse.

### Consumible

Aplica un efecto limitado:

- curación;
- velocidad temporal;
- gravedad temporal;
- reset de dash;
- salto adicional;
- invulnerabilidad breve.

## Capacidad futura

```json
"capabilities": ["items", "weapons"]
```

```json
"content": {
  "items": ["content/items/boost.json"],
  "weapons": ["content/weapons/pistol.json"]
}
```

## Límites recomendados

| Campo | Límite sugerido |
| --- | --- |
| daño | 1–100 |
| intervalo mínimo | 0.08 s |
| cargador | 1–100 |
| recarga | 0.2–10 s |
| velocidad proyectil | 2–60 |
| proyectiles activos | límite global por arma/jugador |
| duración de efecto | límite definido por tipo |

## Input System

Acciones oficiales sugeridas:

```text
Player/UseItem
Player/FireWeapon
Player/ReloadWeapon
Player/Aim
```

No deben definirse bindings arbitrarios desde el mod. El juego ofrece acciones y el jugador las rebindea.

## Editor visual futuro

El editor de menús ya demuestra el patrón correcto:

1. herramienta externa visual;
2. genera JSON permitido;
3. validador comprueba límites;
4. empaquetador crea `.jfmod`;
5. runtime interpreta datos con componentes oficiales.

La misma arquitectura puede reutilizarse para un editor de items y armas sin abrir Unity.
