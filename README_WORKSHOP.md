# JumpFall SDK - Steam Workshop para mods `.jfmod`

Este documento explica como funciona el flujo de Workshop para mods de JumpFall.
El objetivo es que un creador pueda empaquetar un mod con el SDK, subirlo a Steam
Workshop y que el juego lo instale sin tocar archivos internos del juego.

## Que archivo se publica

Un item de Steam Workshop para mods debe incluir uno o mas archivos:

```text
*.jfmod
```

Un `.jfmod` es un archivo ZIP con extension propia. Debe contener el manifiesto
en la raiz:

```text
jumpfall.mod.json
```

No publiques la carpeta fuente completa si no es necesario. Para el juego, el
archivo importante es el `.jfmod` generado por el SDK.

## Crear un `.jfmod`

Desde la carpeta del SDK:

```bash
python jumpfall_sdk.py validate mi-mod
python jumpfall_sdk.py pack mi-mod -o dist/mi-mod.jfmod
```

En Windows tambien puedes usar:

```powershell
py jumpfall_sdk.py validate mi-mod
py jumpfall_sdk.py pack mi-mod -o dist\mi-mod.jfmod
```

El comando `pack` valida primero. Si el mod tiene errores, no se crea el paquete.

## Instalacion manual

Para probar sin Workshop, copia el `.jfmod` en:

```text
Documents/jumpfall/mods/packages/
```

Luego abre JumpFall en PC, presiona `F10` en `Menugame`, actualiza la lista,
activa el mod y reinicia/aplica.

## Instalacion desde Steam Workshop

Cuando el usuario esta suscrito a un item de Workshop, Steam descarga el contenido
en su carpeta interna. JumpFall lee esa carpeta y copia los `.jfmod` a:

```text
Documents/jumpfall/mods/packages/workshop/
```

El nombre instalado usa el ID del item como prefijo:

```text
{workshopId}_00_nombre-del-mod.jfmod
```

Ejemplo:

```text
Documents/jumpfall/mods/packages/workshop/3723053412_00_mi-mod.jfmod
```

El prefijo evita choques entre paquetes con el mismo nombre y permite limpiar el
contenido cuando el usuario se desuscribe.

## Limpieza automatica

Si el usuario se desuscribe de un item, JumpFall borra los `.jfmod` instalados
con ese `workshopId`. Esto evita que queden mods viejos activos por accidente.

Los mods instalados manualmente en:

```text
Documents/jumpfall/mods/packages/
```

no se borran al limpiar Workshop.

## Como aparece en el juego

El gestor de mods escanea estas rutas:

```text
Documents/jumpfall/mods/packages/
Documents/jumpfall/mods/packages/workshop/
```

Los paquetes encontrados aparecen en el gestor `F10`. El jugador puede activar o
desactivar mods, pero los cambios se aplican despues de reiniciar.

## Reglas de seguridad

El runtime de JumpFall valida los paquetes antes de cargarlos:

- el `.jfmod` debe tener extension correcta;
- el manifiesto debe estar en la raiz;
- no se permiten rutas absolutas ni `..`;
- se bloquean ejecutables, DLL, scripts externos y extensiones peligrosas;
- se aplican limites de tamano por paquete, imagen, audio, mapa y manifiesto;
- Lua dentro de `.jfmod` esta deshabilitado hasta que exista un sandbox estable.

## Flujo recomendado para publicar

1. Crea o edita el mod en una carpeta de trabajo.
2. Ejecuta `validate`.
3. Ejecuta `pack`.
4. Prueba el `.jfmod` manualmente en `Documents/jumpfall/mods/packages/`.
5. Sube el `.jfmod` probado al item de Steam Workshop.
6. Suscribete al item desde Steam y verifica que aparezca en el gestor `F10`.

## Compatibilidad

El SDK funciona con Python 3.10 o superior en Windows, macOS y Linux.

El runtime de mods de JumpFall esta pensado para builds de PC:

- Windows;
- macOS;
- Linux.

Android e iOS no cargan `.jfmod` por ahora.

