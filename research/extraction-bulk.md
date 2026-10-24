# Extracción masiva — fase 5

## Estado
**Fase 5 completada.** Se exportaron las texturas, los sprites, las mallas y los sonidos catalogados. No quedan fallos en el diario. Los originales del APK y el OBB se volvieron a comprobar por SHA256 al empezar y al terminar; no se modificaron.

La salida está en `exports/bulk/`. El diario es `journal.sqlite`. El resumen de máquina es `summary.json`, con copia en `research/evidence/extraction/bulk-summary.json`. `failures.jsonl` está vacío.

| Tipo | Recuperados | Fallidos | Omitidos |
| --- | ---: | ---: | ---: |
| Texturas PNG | 3.328 | 0 | 12 |
| Sprites PNG | 47 | 0 | 0 |
| Sonidos WAV | 1.106 | 0 | 0 |
| Mallas OBJ | 4.620 | 0 | 0 |

En disco hay **16.043 archivos** y **5,91 GiB**. Cada malla lleva un MTL. 165 mallas tienen más de una asignación de material, así que hay **1.161 OBJ adicionales** con la otra textura. 12 texturas se omitieron porque ancho o alto es 0; entre ellas está `Font Texture`.

## Cómo está organizado
Cada recurso vive bajo su tipo, el paquete (`apk` u `obb`) y la ruta interna del archivo Unity. El nombre del archivo empieza por el `path_id`.

```text
exports/bulk/textures/obb/assets/bin/Data/sharedassets104.assets/17_school_menu_atlas.png
exports/bulk/models/obb/assets/bin/Data/sharedassets104.assets/34_School_menu_bench2.obj
exports/bulk/audio/obb/assets/bin/Data/sharedassets104.assets/41_Bells_lobby.wav
```

Dos recursos llamados igual no se pisan: en el lote de prueba, las dos texturas `Coins_Shop_1` salieron a rutas distintas y sus píxeles no coinciden. Si una malla tiene varias asignaciones de material, la preferida conserva el nombre corto y las demás añaden `__archivo_path`, por ejemplo `4_PixlGun_Mesh__8648_28.obj`.

El MTL usa una ruta relativa a la PNG. La del banco apunta a `17_school_menu_atlas.png` y esa ruta se resolvió dentro de `exports/bulk/`.

## Qué se comprobó
Antes de la pasada completa se exportó un lote pequeño al mismo directorio: las dos muestras ya aprobadas, una textura sin dimensiones, una malla de dos submeshes, dos texturas con el mismo nombre, dos sprites y dos sonidos más. Una segunda ejecución de ese lote dejó **0 pendientes**.

Contra las muestras aprobadas:

- `School_menu_bench2`: las 312 posiciones del OBJ coinciden con `exports/samples/models/School_menu_bench2.obj`.
- `PixlGun_Mesh`: las 394 posiciones coinciden en las dos variantes. La variante `__8648_28` usa la textura `PixelGun_2.0_map`, que es la que se validó. La otra usa `map_Pixlgun`, presente en otro `SkinnedMeshRenderer` del mismo mesh.
- Los píxeles de `school_menu_atlas` y de `PixelGun_2.0_map` coinciden con los PNG aprobados. El archivo PNG no es idéntico porque esta pasada usa compresión rápida; la comparación es de píxeles.
- `PixlGun_Shoot.wav` es idéntico al WAV aprobado: PCM 16 bits, mono, 44.100 Hz, 44.979 frames.
- `Bells_lobby.wav` es PCM 16 bits, mono, 32.000 Hz, 38.815 frames, los mismos parámetros documentados en la fase 4.

En toda la pasada, cada PNG se reabrió y sus píxeles se compararon con la imagen decodificada. Cada OBJ se comparó con la malla procesada por UnityPy, con el reflejo de X y el winding invertido. Cada WAV se abrió; los 1.106 son WAV y ninguno está en silencio. Al cerrar, se volvieron a leer los SHA256 guardados en el diario. No se pasó el catálogo completo por Blender.

La primera pasada rechazó tres mallas (`horisont` dos veces y `Embiant`) porque sus UV de lightmap superan las 10.000 unidades y el redondeo a nueve cifras del OBJ pasaba de una tolerancia absoluta de `1e-5`. La comprobación ahora es relativa a la magnitud. La reanudación exportó solo esas tres y el diario quedó sin fallos.

## Reanudar
Desde la raíz, con el inventario ya preparado:

```bash
uv run --locked -m tools.export_bulk --profile trial --output exports/bulk
uv run --locked -m tools.export_bulk --output exports/bulk
```

Un ítem `ok` no se repite si sus archivos siguen en su sitio, el SHA256 coincide y la revisión del exportador es la misma. Un ítem `failed` se reintenta. Un ítem `skipped` no, salvo que cambie la revisión del exportador. Si `exports/bulk/` existe y no hay `journal.sqlite`, la herramienta se niega a mezclarse con ese directorio. No toca `exports/samples/` ni `exports/samples-weapon/`.

## Limitaciones
El OBJ es la geometría estática o la pose de reposo. No hay esqueletos, pesos ni animaciones. **697** mallas tienen poses de bind y quedan marcadas `rest_pose_only`.

**2.773** mallas no tienen un `MeshRenderer` o `SkinnedMeshRenderer` resuelto en el inventario, así que su MTL no lleva textura del juego. Puede haber usos en partículas u otros componentes que este grafo no cubre.

El material solo guarda el tinte y `_MainTex`. No reproduce el shader ni la iluminación. En **7** materiales la escala de UV no es 1 y en **8** el desplazamiento no es 0; esos valores van como opciones `-s` y `-o` de `map_Kd`, y hay visores que las ignoran. **103** mallas tienen color de vértice y el OBJ no lo incluye. **68** no tienen normales y **4** no tienen UV. **111** huecos de material no se pudieron resolver y **105** mallas no traen un material por submesh. **2** mallas tenían coordenadas no finitas; se sustituyeron por 0 y quedó anotado.

**44** de 47 sprites no pudieron salir por la malla ajustada de UnityPy (`AssertionError` al leer los vértices del sprite). Se recortó el rectángulo de la textura y se volteó en vertical, igual que el recorte de UnityPy, sin la máscara del polígono. Tres sprites sí salieron por `sprite.image`.

No se exportaron los 5 cubemaps, las 12 fuentes ni el `RenderTexture`. El inventario marca `vertex_count` 0 en **619** mallas; UnityPy reconstruyó vértices, el OBJ pasó la comprobación y se conservaron.

Una textura enlazada y un OBJ que coincide con la malla no prometen la apariencia del juego. El lote de prueba se miró: la textura del arma, el mapa alternativo, el sprite `Checkmark` y `teleport` se ven como imágenes de juego. El resto se comprobó por formato, dimensiones y geometría, no uno a uno en Blender.

## Repetir
`uv run --locked -m unittest discover -s tests -v` incluye las pruebas de nombres, de reanudación y de la conversión OBJ. En esta fase la suite tiene **33** casos y pasó.
