# Plan de conversión OBJ a GLB

## Objetivo
Convertir los modelos ya extraídos en OBJ y MTL a glTF 2.0 binario (`.glb`), conservando la forma, las UV, las normales y las texturas, para cargarlos en el navegador sin parsear texto ni volver a transformar ejes.

La fuente es `exports/bulk/models/`: **5.781 OBJ** con su MTL. Los PNG siguen en `exports/bulk/textures/` y el GLB solo los referencia. El destino es `exports/gltf/`. Los OBJ, los PNG, los WAV y los sprites no se mueven ni se reescriben.

**No incluye:** pasar por FBX, incrustar o recomprimir PNG, KTX2, meshopt ni cuantización, esqueletos, animaciones, shaders del juego, ni volver a extraer el APK o el OBB. Los WAV se quedan en WAV.

## Decisiones
- El OBJ ya está en Y hacia arriba, con la X reflejada. El GLB copia esos números. No se gira otra vez.
- No se usa Blender ni `obj2gltf`. Esos caminos leen la imagen, suelen incrustarla y pueden cambiar el eje. El convertidor entiende solo el OBJ que escribió la extracción: triángulos, el mismo índice para posición, UV y normal, y un MTL con `Kd`, `d` y `map_Kd`.
- Cabe en el proyecto uv, sin dependencia nueva. `npx gltf-validator` se usa solo sobre las muestras, si hay red.
- La ruta de la textura se recalcula desde la carpeta del GLB hasta el PNG. No se copia el `../` del MTL, porque el GLB no vive junto al OBJ.
- Nombre: se quita el segmento `models/` y se cambia la extensión. `exports/bulk/models/obb/assets/bin/Data/.../34_School_menu_bench2.obj` pasa a `exports/gltf/obb/assets/bin/Data/.../34_School_menu_bench2.glb`.
- Material: color `Kd` y opacidad `d` tal como están en el MTL, metálico 0 y rugosidad 1. No se convierte el color a lineal. Si hay `-s` o `-o`, se escriben en `KHR_texture_transform`. Si `d` es menor que 1, el material es transparente (`BLEND`).
- Sin UV no hay coordenada ni textura. Sin normales no hay accessor de normales. Un primitivo por submesh, en el orden del OBJ. Cada variante `__archivo_path` sigue siendo otro GLB.
- Si el diario de la extracción marca filtro Point (`filter_mode` 0), el sampler es `NEAREST`. El resto, `LINEAR`.
- Índices `uint16` por debajo de 65.536 vértices y `uint32` a partir de ahí. La malla más grande tiene 63.266 vértices.
- Se puede reanudar. `exports/gltf/journal.sqlite` guarda el OBJ, su SHA256 y el del GLB. Si coinciden, no se repite. Un modelo que falla queda anotado y el lote sigue. El destino no puede ser `exports/bulk/`, `exports/samples/` ni `exports/samples-weapon/`.

Casos ya contados en el diario de la extracción: 8 materiales con escala de UV distinta de 1, 8 con desplazamiento, 69 con opacidad distinta de 1, 4 mallas sin UV y 68 sin normales.

## Plan y checklist
Las casillas marcadas están completadas. Las demás son los pasos que faltan. Esta iteración no ha empezado.

### 1. Leer el OBJ y el MTL
- [ ] Leer posiciones, UV, normales y un grupo de triángulos por cada `usemtl`.
- [ ] Leer `Kd`, `d`, `map_Kd` y, si existen, `-s` y `-o`, resolviendo la ruta del PNG dentro de `exports/`.
- [ ] Rechazar una cara que no sea un triángulo, un índice distinto para posición y UV, o una ruta que se salga de `exports/`.

### 2. Escribir el GLB
- [ ] Un mesh, un nodo y un primitivo por submesh, con `min` y `max` en las posiciones y los chunks alineados a 4 bytes.
- [ ] Referenciar el PNG sin copiarlo. Aplicar escala, desplazamiento, transparencia y filtro según las decisiones de arriba.
- [ ] Comprobar en una prueba pequeña que, al releer el GLB, la geometría coincide con el OBJ y el PNG no cambió.

### 3. Validar las muestras conocidas
- [ ] Convertir el banco (`34_School_menu_bench2`, 312 vértices) y las dos variantes de `PixlGun_Mesh` (394 vértices).
- [ ] Confirmar que la variante corta usa `map_Pixlgun` y `__8648_28` usa `PixelGun_2.0_map`, y que esos PNG conservan su SHA256.
- [ ] Pasar esos tres GLB por `gltf-validator` si hay red, y anotar si no se pudo ejecutar.

### 4. Preparar el lote
- [ ] Convertir varios OBJ en paralelo. El diario lo escribe un solo proceso.
- [ ] Reanudar sin repetir un GLB cuyo OBJ y cuyo archivo siguen coincidiendo con el SHA256 guardado.
- [ ] Probar, en un directorio temporal, que un OBJ inválido queda anotado y que el resto se escribe.

### 5. Ejecutar la conversión
- [ ] Probar antes un grupo con una malla sin normales, una sin UV, una con opacidad, una con escala o desplazamiento de UV, y `Devostator_rocket_mesh` (dos submeshes).
- [ ] Convertir los 5.781 OBJ.
- [ ] Comprobar que hay un GLB por OBJ, que no quedan archivos a medias, que cada textura referenciada existe y que una segunda pasada deja 0 pendientes.

### 6. Cerrar la iteración
- [ ] Escribir el resumen con conteos reales, fallos y límites en `research/extraction-gltf.md`.
- [ ] Dejar el comando de reanudación en el README: `uv run --locked -m tools.export_gltf --output exports/gltf`.

## Dónde estamos y qué sigue
**Esta iteración no ha empezado.** La extracción de la [iteración 0001](0001-extraccion-de-recursos.md) está terminada y es la fuente. No hay que repetir el inventario ni los OBJ.

El primer trabajo es el lector y el escritor, y después las dos muestras ya aprobadas. El lote de 5.781 espera a que esas muestras coincidan con el OBJ.

## Documentación de apoyo
- [Extracción masiva](../../research/extraction-bulk.md).
- [Muestras aprobadas](../../research/extraction-samples.md).

Un GLB que coincide con el OBJ conserva la forma y la textura extraídas. No recupera el shader, el esqueleto ni la animación del juego. La copia comprimida para publicar, si hace falta, será otra iteración.
