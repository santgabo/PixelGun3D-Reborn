# Muestras exportadas y validación — fases 3–4

## Estado actual
**Fase 3 completada.** Se exportaron una textura, una malla estática con material y un sonido. La importación, las UV, la textura y dos renders se comprobaron en Blender. **Fase 4 completada: el usuario confirmó que puede ver el modelo y la imagen y escuchar el sonido; las muestras están aprobadas. No se inició la extracción masiva.**

No hubo bloqueos de exportación para estas tres muestras. Los SHA256 del APK y el OBB siguen coincidiendo con los originales.

## Archivos para revisar
Todos están bajo `exports/samples/`:

| Recurso | Ruta |
| --- | --- |
| Modelo listo para abrir en Blender, con textura incrustada | `validation/School_menu_bench2.blend` |
| Vista frontal/oblicua | `validation/School_menu_bench2.png` |
| Vista posterior | `validation/School_menu_bench2_back.png` |
| Malla reutilizable OBJ | `models/School_menu_bench2.obj` |
| Material MTL básico | `models/School_menu_bench2.mtl` |
| Textura PNG | `textures/school_menu_atlas.png` |
| Sonido WAV | `audio/Bells_lobby.wav` |

**Para mover el OBJ, conserva la estructura de `models/` y `textures/`:** el MTL usa una ruta relativa al PNG. El `.blend` es autónomo: se abrió una copia en una carpeta temporal sin el PNG externo y la textura incrustada cargó correctamente.

## Comprobaciones realizadas
### Textura
- `school_menu_atlas`, 1024×1024 RGBA, formato Unity 34.
- PNG decodificado y vuelto a abrir; sus píxeles coinciden con la imagen decodificada del recurso.
- Atlas inspeccionado visualmente y cargado en el material de Blender.

### Malla y material
- `School_menu_bench2`: **312 vértices, 156 triángulos, 312 UV y 312 normales** en OBJ.
- Posiciones, UV, normales e índices contrastados con el recurso de Unity, teniendo en cuenta la conversión de ejes y winding de UnityPy.
- Blender conserva los 312 vértices, 156 triángulos y 468 esquinas UV; sin triángulos degenerados detectados.
- Un material `school_menu_atlas`, con la textura conectada; sin esqueletos ni animaciones.
- Dos renders revisados: malla completa dentro del encuadre y textura visible en tablas y soportes. La previsualización usa filtrado `Closest`; el recurso original usa Point (`m_FilterMode=0`).
- `.blend` reabierto en un proceso independiente sin acceso al PNG externo; su PNG incrustado tiene el mismo SHA256 que el exportado.

El `.blend` añade únicamente cámara y luces de previsualización: **no es una reconstrucción de una escena del juego**. La malla conserva sus coordenadas locales, con la conversión de ejes correspondiente.

### Audio
- `Bells_lobby.wav`: PCM de 16 bits, mono, 32.000 Hz, **38.815 frames / 1,21296875 segundos**.
- Duración y parámetros coinciden con los metadatos del AudioClip, dentro de un frame de tolerancia.
- Datos completos, señal no silenciosa y ninguna muestra en los extremos de saturación PCM.
- `afinfo` de macOS reconoce el WAV y sus parámetros.
- **Escucha manual confirmada por el usuario.** La aprobación se registra en el resumen consolidado; no se extiende automáticamente al resto del catálogo.

## Cobertura y límites
Solo se probaron **una textura, una malla rígida de un submesh con UV/normales y un clip de audio**. Esto no valida automáticamente todos los formatos, modelos de múltiples materiales, mallas sin UV, personajes ni los 1.106 clips del inventario.

El MTL conserva una textura difusa y un tinte básicos. No replica el shader original, sus propiedades personalizadas ni la iluminación del juego. No se comparó el resultado con una captura del juego; no se promete apariencia idéntica. La muestra de malla no contiene colores de vértice; este exportador no los incorpora al OBJ.

Se ajustaron detalles de validación de Blender 5.2: carga diferida de imágenes antes de comprobar `has_data`, encuadre completo mediante proyección de los límites, distinción entre la textura del material y la imagen interna `Render Result`, y uso de nodos sin las propiedades `use_nodes` obsoletas. No fueron fallos del contenido exportado.

## Repetir las pruebas
Desde la raíz del proyecto; el destino debe ser nuevo:

```bash
uv run --locked -m tools.export_samples --output exports/samples-check

uv run --locked /Applications/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup --disable-autoexec --offline-mode \
  --python-exit-code 1 --python tools/validate_sample_blender.py \
  -- --samples exports/samples-check

uv run --locked -m unittest discover -s tests -v
```

Las 23 pruebas originales pasaron al exportar las muestras. Después de migrar a proyecto uv, la suite actual tiene **26 casos**, todos superados. Los scripts rechazan sobrescribir sus destinos. No requieren Unity Editor ni nuevas instalaciones. Blender se lanza mediante uv, utiliza su Python integrado y se ejecuta sin abrir su GUI ni ejecutar código del juego.

## Informes y procedencia
- `exports/samples/validation-summary.json`: estado consolidado y limitaciones actuales.
- `exports/samples/manifest.json`: procedencia, hashes y comprobaciones al terminar la exportación; su indicador de Blender pendiente corresponde a ese instante, no al estado consolidado posterior.
- `exports/samples/validation/blender-check.json`: comprobaciones de importación y render; la revisión visual posterior se registra en el resumen consolidado.
- `exports/samples/validation/portability-check.json`: reapertura aislada del `.blend`.
- Copias persistentes en `research/evidence/extraction/sample-{export,blender-check,portability-check,validation-summary}.json`.

Los recursos pertenecen al OBB, `assets/bin/Data/sharedassets104.assets`: Mesh pathID 34, Texture2D 17, Material 7 y AudioClip 41. El audio lee el rango 0–14.272 de `sharedassets104.resource`. Los hashes y rutas completas están en los informes. `sample-candidates.json` conserva la selección histórica de la fase 2.

## Siguiente paso
El usuario ya aprobó el modelo, la imagen y el sonido. Tras la preparación de uv y Git, el siguiente trabajo será la extracción por lotes manteniendo procedencia, nombres sin colisiones y registro de fallos por recurso. La cobertura restante se validará por tipos y formatos, sin prometer recuperación total.

## Fuentes técnicas
- Exportación UnityPy: https://github.com/K0lb3/UnityPy#important-object-types
- OBJ, UV y winding: implementación instalada `UnityPy/export/MeshExporter.py` (1.25.4).
- Audio: `UnityPy/export/AudioClipConverter.py` y `fmod_toolkit/fmod.py`, instalados.
- Importación OBJ y guardado Blender: https://docs.blender.org/api/current/bpy.ops.wm.html
- Render: https://docs.blender.org/api/current/bpy.ops.render.html
- Encuadre: https://docs.blender.org/api/current/bpy_extras.object_utils.html#bpy_extras.object_utils.world_to_camera_view
- Ejecución sin GUI: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
