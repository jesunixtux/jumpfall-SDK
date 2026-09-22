# Seguridad

Los mods son datos no confiables. El SDK y el runtime rechazan traversal de rutas,
enlaces simbólicos, ejecutables, DLL, C#, AssetBundles y bibliotecas nativas.
Lua está deshabilitado en `.jfmod`; no existe un sandbox oficial habilitado.

Las piezas del Level Editor solo pueden heredar arquetipos 2D permitidos y aplicar
sprite, color y escala declarativos. No se cargan prefabs ni componentes externos.

No publiques una vulnerabilidad junto con un paquete de prueba activo. Repórtala
de forma privada al mantenedor y adjunta la salida de `jumpfall-sdk validate` sin
datos personales ni archivos propietarios del juego.
