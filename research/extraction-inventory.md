# Inventario de recursos — fase 2

## Resultado
**Fase 2 completada, sin errores de lectura registrados.** Se prepararon copias de los datos Unity de ambos paquetes y se catalogaron sus objetos, nombres, dependencias de archivo y determinadas referencias de recursos. Esta fase no exportó PNG, OBJ ni audio. Esas primeras muestras ya se generaron después, en la fase 3; resultados y estado de validación en [extraction-samples.md](extraction-samples.md).

| Cobertura | Cantidad |
| --- | ---: |
| Entradas originales de APK + OBB | 10.391 |
| Entradas bajo `assets/bin/Data/` copiadas y verificadas por CRC | 9.804 |
| Grupos `.splitN` recompuestos en orden numérico | 176 |
| Archivos resultantes preparados | 9.214 |
| Archivos serializados de Unity | 8.165 |
| Otros archivos de datos, streams y ensamblados | 1.049 |
| Objetos serializados catalogados | 490.030 |

Las otras **587 entradas** permanecen listadas en el manifiesto, pero no se copiaron: están fuera de `assets/bin/Data/` e incluyen archivos de Android y recursos auxiliares. No se ha realizado un inventario de objetos gráficos independiente para esas entradas.

### Recursos de interés
| Tipo Unity | Objetos |
| --- | ---: |
| Mesh | 4.620 |
| Texture2D | 3.340 |
| AudioClip | 1.106 |
| Material | 2.165 |
| Sprite | 47 |
| Font | 12 |

Estas cifras cuentan **objetos serializados**, no modelos únicos ni recursos deduplicados; incluyen recursos internos del motor y nombres repetidos. Todos los Mesh, Texture2D, AudioClip y Material tienen nombre legible. Los tipos de animación aparecen en el recuento general, pero no se interpretaron sus clips ni se exportarán.

### Referencias y versiones
- **34.609 referencias externas de archivo**, todas resueltas en los datos preparados. La ruta `library/unity default resources` se asoció por basename inequívoco al recurso del APK; las rutas se conservan para auditar esa asociación.
- **78.205 referencias seleccionadas entre objetos**: 77.505 resueltas y 700 nulas legítimas. Incluyen 4.656 asociaciones de nombres lógicos del ResourceManager, sin sobrescribir nombres repetidos.
- **1.106 streams de audio** localizados: todos tienen archivo de destino y rangos `offset + size` dentro del archivo. No se ha probado todavía su decodificación.
- **0 referencias sin resolver y 0 errores** dentro de la cobertura examinada.
- 8.164 archivos serializados indican Unity **5.3.7p1**. `apk/assets/bin/Data/unity default resources` indica **5.3.6p2**; también se leyó sin errores.

No se carga todo el juego en un único Environment de UnityPy: cada archivo se interpreta por separado y las referencias se resuelven mediante índices propios. Así se conserva la identidad `(paquete, ruta interna, path_id)` y se evitan colisiones por basename. No aparecieron basenames duplicados en estos datos.

## Archivos generados
- `work/prepared/manifest.json`: origen, entradas ZIP, CRC, hashes y relación entre fragmentos y archivos preparados.
- `work/prepared/apk/assets/bin/Data/` y `work/prepared/obb/assets/bin/Data/`: copias separadas; unos 1,4 GB en conjunto.
- `work/inventory/resources.sqlite`: catálogo consultable, unos 56 MB.
- `work/inventory/summary.json`: resumen completo de recuentos y cobertura.
- `work/inventory/errors.jsonl`: errores de lectura; vacío en esta ejecución.
- `work/inventory/unresolved-references.jsonl`: referencias rotas o streams fuera de rango; vacío en esta ejecución.
- `research/evidence/extraction/inventory-summary.json`: copia persistente del resumen.
- `research/evidence/extraction/sample-candidates.json`: candidatos concretos para las próximas pruebas, todavía sin exportar.

En SQLite, `files` conserva procedencia y hashes; `objects` usa la clave compuesta `(file_id, path_id)`; `externals`, `links` y `streams` conservan referencias originales y su resolución. `errors` registra incidencias por archivo y objeto. `objects.details_json` contiene dimensiones de texturas, cantidades de vértices y metadatos de audio cuando corresponde. Los identificadores numéricos `file_id` pertenecen a este catálogo; para identificar un recurso de forma portable, usar paquete, ruta y `path_id`.

## Reproducir
Desde la raíz, con el entorno de la fase 1 disponible:

```bash
# Usar estos destinos solo si todavía no existen.
uv run --locked tools/prepare_assets.py
uv run --locked -m tools.inventory_assets

# Suite actual: 26 casos, sin tocar los originales.
uv run --locked -m unittest discover -s tests -v
```

Ambas herramientas rechazan sobrescribir un destino existente. Para una ejecución adicional sin borrar nada:

```bash
uv run --locked tools/prepare_assets.py --output work/prepared-check
uv run --locked -m tools.inventory_assets --prepared work/prepared-check --output work/inventory-check
```

El inventariador devuelve código 0 cuando termina sin incidencias y 1 cuando produce un inventario con advertencias; los detalles quedan en los registros. Las salidas se publican desde un directorio temporal solo al terminar. La preparación comprueba los SHA256 de los originales antes y después, y el inventario los vuelve a comprobar al finalizar. Cada copia preparada se verifica por SHA256 al leerla. Los originales no se modificaron.

## Validación realizada y límites
- Pruebas de orden numérico, fragmentos ausentes o ambiguos, rutas inseguras, enlaces y sobrescrituras.
- Pruebas de resolución de referencias entre archivos, referencias nulas/inválidas, nombres repetidos, errores de campos y streams fuera de rango.
- Prueba integrada previa con cinco archivos reales que contienen mallas, texturas, materiales y audio.
- Integridad SQLite y claves foráneas correctas; cantidades de archivos, bytes y objetos contrastadas contra manifiesto y tablas.
- Cadena concreta comprobada: malla `School_menu_bench2` → material `school_menu_atlas` → textura `school_menu_atlas`.

**No es un análisis de todos los campos o de todas las referencias del juego.** Se interpretan diez tipos relevantes para recursos y materiales; del resto se intenta leer el nombre. No se reconstruyen escenas ni esqueletos, ni se analizan campos personalizados de scripts. Las relaciones de partículas, interfaces personalizadas y otros componentes fuera de esos tipos no están cubiertas por el grafo de referencias seleccionado.

Un nombre legible, una referencia resuelta o un rango válido **no demuestran que un recurso se exporte, se vea o suene correctamente**. Eso corresponde a las fases 3–4.

## Muestras seleccionadas en esta fase
Los candidatos siguientes ya se exportaron en la fase 3. Esta lista conserva la selección previa; consultar [extraction-samples.md](extraction-samples.md) para el estado actual.

1. Exportar la textura `school_menu_atlas` a PNG.
2. Exportar la malla estática `School_menu_bench2` a OBJ y asociar esa textura mediante un material MTL básico. Tiene 312 vértices y un submesh en los metadatos; UV y apariencia aún pendientes de validar.
3. Exportar `Bells_lobby` a un archivo de audio reproducible.
4. Comprobar textura, audio y modelo en Blender antes de decidir la extracción masiva.

Los tres recursos están en el OBB, en `assets/bin/Data/sharedassets104.assets`; el sonido utiliza `sharedassets104.resource`. Sus identificadores y metadatos están en `sample-candidates.json`. No requieren recuperar esqueletos ni animaciones.

## Fuentes técnicas
- API de carga, objetos y nombres: https://github.com/K0lb3/UnityPy#important-classes
- Conversión y tipos de recursos: https://github.com/K0lb3/UnityPy#important-object-types
- Campos y semántica contrastados con UnityPy **1.25.4 instalado**: `files/SerializedFile.py`, `files/ObjectReader.py`, `classes/PPtr.py`, `classes/generated.py` y esquemas locales de `helpers/Tpk.py`.
