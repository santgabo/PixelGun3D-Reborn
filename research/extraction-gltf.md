# Conversión OBJ a GLB — iteración 0002

## Estado
**Completada.** Los 5.781 OBJ de `exports/bulk/models/` están convertidos a `exports/gltf/`, uno por OBJ, con la misma ruta sin el segmento `models/`. No hay fallos, ni archivos `.partial`, ni texturas referenciadas que falten. Una pasada posterior deja **0 pendientes** (5.781 omitidos por SHA256). Los OBJ, MTL, PNG, WAV y sprites no se tocaron.

La conversión tarda unos 33 s con 12 procesos. El resumen de máquina es `exports/gltf/summary.json`, con copia en `research/evidence/extraction/gltf-summary.json`. El código es `tools/export_gltf.py` y las pruebas están en `tests/test_export_gltf.py`.

| Dato | Valor |
| --- | ---: |
| GLB escritos | 5.781 |
| Vértices | 47.301.539 |
| Triángulos | 26.829.851 |
| Primitivos (submeshes) | 80.596 |
| GLB con más de un primitivo | 1.766 |
| Tamaño en disco | 1,59 GiB |
| PNG distintos referenciados | 1.362 |
| GLB con textura | 2.826 |
| Mallas sin UV / sin normales | 4 / 72 (las 4 sin UV también carecen de normales) |
| GLB con material transparente (`BLEND`) | 69 |
| GLB con `KHR_texture_transform` | 14 |
| Índices `uint32` | 0 (la mayor malla tiene 63.266 vértices) |

Los 4 sin UV y los 68 con UV pero sin normales coinciden con lo contado en la extracción.

## Qué hace el convertidor
- Copia posiciones y normales del OBJ sin girar ejes. Los índices y el orden de los triángulos tampoco cambian.
- **Renormaliza las normales que no son unitarias**: un vector cuya longitud se aparta de 1 más de 0,006 se divide por su longitud. Los demás se copian tal cual. Afectó a 21 GLB y 42 vectores (longitudes de hasta 0,990). Un vector nulo no se corrige.
- **Voltea la V de las UV** (`v' = 1 - v`). El OBJ y Unity cuentan la V desde abajo; glTF, desde arriba, y el PNG se guardó en orientación normal. Es la única transformación. La escala y el desplazamiento de UV del MTL pasan a `KHR_texture_transform` con la misma conversión: `scale = (sx, sy)`, `offset = (ox, 1 - sy - oy)`.
- Un mesh, un nodo y un primitivo por `usemtl`, en el orden del OBJ. Las posiciones, UV y normales se comparten entre primitivos.
- Material: `Kd` y `d` tal cual, metálico 0, rugosidad 1; `d < 1` pasa a `BLEND`. Sin UV no se escribe textura.
- La textura se referencia por ruta relativa al GLB (`../../…/bulk/textures/…png`), sin incrustar ni copiar el PNG. Sampler `NEAREST` si el diario de la extracción marca `filter_mode` 0 (2.846 texturas) y `LINEAR` en el resto (482).
- Rechaza una cara que no sea triángulo, índices distintos para posición, UV y normal, una ruta de textura fuera de `exports/` o que no existe, y un `usemtl` ausente del MTL. El lote sigue y el fallo queda en el diario.
- Reanudación: `exports/gltf/journal.sqlite` guarda el SHA256 del OBJ, del MTL y del GLB y la revisión del convertidor. Se rechaza como destino `exports/bulk`, `exports/samples`, `exports/samples-weapon` o un directorio sin diario que ya tenga archivos.

## Comprobaciones
- **Muestras aprobadas.** `34_School_menu_bench2` (312 vértices) y las dos variantes de `PixlGun_Mesh` (394). Releídos los GLB, posiciones, normales e índices coinciden con el OBJ y la V es `1 - v`. La variante corta apunta a `1_map_Pixlgun.png` y `__8648_28` a `1_PixelGun_2.0_map.png`; los tres PNG conservan el SHA256 del diario de la extracción. Las tres texturas son Point, así que el sampler es `NEAREST`.
- **Grupo previo.** Antes del lote se convirtieron una malla sin normales (`Skull`), una sin UV (`Icosphere`), una con opacidad (`Capsule`), dos con escala o desplazamiento de UV (`Snowball`, `Lava`), `Devostator_rocket_mesh` (dos primitivos) y una combinada de 62.786 vértices y 26 primitivos.
- **Pruebas unitarias.** `uv run --locked -m unittest discover -s tests` pasa (42 pruebas): ida y vuelta de la geometría, PNG sin cambios, alineación a 4 bytes, `uint32`, sin UV o normales, transformación de textura, entradas rechazadas, un OBJ inválido anotado mientras el resto se escribe, reanudación y destinos prohibidos.
- **`gltf-validator`.** Se ejecutó con red sobre **los 5.781 GLB**: 5.760 sin errores ni avisos y 21 con error `ACCESSOR_VECTOR3_NON_UNIT` en las normales. Eran mallas `Combined_Mesh_root_scene` (nivel 58 y vecinos) cuyas normales, cuantizadas por Unity, quedaban hasta un 1 % cortas. Tras renormalizarlas (revisión 4 del convertidor), **los 5.781 pasan sin errores ni avisos**.

## Límites
- No recupera el shader, el esqueleto ni la animación del juego. Una malla con bind pose sale en reposo, como en el OBJ.
- Las normales de esos 21 GLB ya no son idénticas a las del OBJ (42 vectores corregidos, ≤ 1 % de diferencia). El resto de las normales sí lo es.
- El modo de envoltura (`wrap`) de la textura no se lee del diario: el sampler usa el valor por defecto de glTF (repetir).
- `KHR_texture_transform` figura en `extensionsUsed` pero no en `extensionsRequired`; un visor sin la extensión ignora la escala y el desplazamiento de esos 14 modelos.
- El PNG original no se recomprime: el GLB pesa poco y depende de la carpeta `exports/bulk/textures/`. Mover `exports/gltf/` obliga a mover también `exports/bulk/` con la misma estructura. Una copia comprimida para publicar sería otra iteración.
