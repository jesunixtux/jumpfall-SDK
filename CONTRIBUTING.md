# Contribuir

1. Abre un issue antes de cambiar un contrato público.
2. Mantén compatibilidad hacia atrás dentro de `schemaVersion` 1.x.
3. Ejecuta `python -m unittest discover -s tests -v`.
4. Valida `templates/content-mod` con la CLI.
5. Actualiza runtime, README, changelog, schemas, plantilla y wiki afectados.

No incluyas assets extraídos del juego base, DLL, C#, AssetBundles, ejecutables ni
binarios nativos. Un arquetipo nuevo para el Level Editor debe existir primero en
el juego base y conservar los límites 2D del proyecto.
