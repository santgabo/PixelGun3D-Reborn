# Inventario de recursos — PARTIAL

Corrida **20261009T191951Z**. `RUN` = `./.lab/runs/20261009T191951Z/`, privado. Origen: `./unpacked/{apk,obb}/assets/bin/Data`, verificado contra APK/OBB originales. Herramientas: Python estándar **3.14.4**, UnityPy **1.25.4**, AssetRipper Free **2.0.0**.

## Staging — PASS limitado a bytes/cabeceras

`./tools/prepare_unity_data.py` y sus pruebas sintéticas se ejecutaron RED→GREEN. Comando reproducible, con destinos **nuevos**:

```bash
python3 ./tools/prepare_unity_data.py --apk-data "$APK_DATA" --obb-data "$OBB_DATA" \
  --output-data "$RUN/staging/Data" --manifest "$RUN/staging/manifest.json"
python3 -m unittest discover -s ./tests -v
```

Se rechazan huecos/duplicados de índice, colisiones APK/OBB y archivo-fragmentos, destinos existentes, solapamientos (incluyendo `..`) y symlinks. Copia independiente por bloques, no hardlinks; publicación después de validar; manifiesto completo solo al final. El entorno debe ser privado y de un único escritor, con entradas inmutables.

| Verificación real | Resultado |
|---|---:|
| Archivos finales | 9.214 |
| Bytes finales | 1.450.006.401 |
| Grupos / fragmentos | 176 / 766 |
| Grupos Unity v15 con tamaño consistente | 175 |
| Grupo FSB5, no serializado Unity | `sharedassets94.resource` |
| Niveles | `level0`–`level108`, 109 |
| Archivos hexadecimales | 7.943 |

Cada archivo conserva `relative_path`, fuentes APK/OBB, tamaños, SHA-256, formato y alcance de validación. Todos los hashes de fuentes coinciden con la línea base de tarea 1. Evidencia: `staging/manifest.json` y `verification.json`. Esto **no valida semánticamente todos los objetos** ni demuestra integridad de audio FSB5.

## Piloto y cobertura

Inventariados cinco archivos: `globalgamemanagers`, `globalgamemanagers.assets`, `level0`, `sharedassets0.assets`, `sharedassets1.assets`. La ampliación incorporó el archivo de MonoScripts referenciado y el audio ausente del primer conjunto.

- **3.524 objetos** enumerados; **659 errores de lectura**: un PlayerSettings y 658 MonoBehaviour.
- **8.160 archivos serializados pendientes** de inventario, enumerados explícitamente en `assets/coverage.json`. No se hizo exportación masiva.
- Cada registro de `assets/inventory.jsonl` conserva origen, `path_id`, class_id/tipo, nombre cuando se pudo leer, versión Unity, herramienta, corrida y estado/error. Checkpoints por archivo bajo `assets/checkpoints/`; el comando Python exacto está en `logs/unitypy-inventory-*.json`.

## Muestras

| Archivo + path_id | Tipo | Resultado técnico |
|---|---|---|
| `sharedassets0.assets` + **8** | Texture2D | PNG 1024×1024, reabierto y decodificado con Pillow; coincide con dimensiones serializadas. |
| `sharedassets0.assets` + **19** | Mesh | OBJ, 6 vértices/8 caras; índices de vértice/UV/normal válidos y conteo contrastado con MeshHandler. |
| `sharedassets1.assets` + **42** | AudioClip | WAV PCM, 44.100 Hz, mono, duración 0,742 s; decodificación y estructura WAV comprobadas. |
| `level0` + **15** | MonoBehaviour | Lectura completa de este objeto y enlace a `globalgamemanagers.assets` + **750**, `Assembly-CSharp.dll::DeviceOrientationMonitor`; campo serializado nativo `m_Enabled=1`. C# presente y verificado. |

Salidas por `source_file/path_id`, no por nombres amigables. Evidencia: `assets/pilot.json`, `mesh-validation.json` y `pilot/`. No se revisaron visualmente la textura/malla ni se escuchó el audio; no se afirma fidelidad perceptual. El primer chequeo de malla falló por usar `Mesh.m_VertexCount`, propiedad inexistente en esta API; se conservó el fallo y después se validó usando el **MeshHandler** documentado por el código instalado.

## Parsers y referencias

- **PlayerSettings:** vuelve a fallar en el conjunto completo de staging. La prueba independiente con lector Python puro también termina leyendo fuera de los datos (`struct.error`); desactivar el lector C no resuelve el problema. No se atribuye a corrupción del original ni se cambia el parser a ciegas.
- **MonoBehaviour:** faltan layouts personalizados; las discrepancias de bytes leídos no se silencian. Se obtuvieron seis enlaces de cabecera en level0 con `check_read=False`, etiquetados **solo referencia de cabecera**, no lectura completa ni recuperación de campos propios. `DeviceOrientationMonitor` se leyó también con validación completa en el piloto.
- **TypeTreeGeneratorAPI:** se evaluó la vía documentada con las 27 DLL de esta versión; la dependencia opcional no está instalada y el plan prohíbe instalarla. Generación **NOT_RUN**, sin layouts inventados.
- **AssetRipper:** importó copias independientes del mismo conjunto de cinco archivos y Managed, reconoció Mono/5.3.7p1/27 ensamblados y terminó lectura/procesamiento. El piloto reducido produjo **7.999 avisos de dependencias omitidas**; no se interpretan como corrupción. El staging completo se conserva separado. Importación, no exportación/reconstrucción integral. UI solo loopback, salida rc0 y listener cerrado, con evidencia en `logs/assetripper-session.json`.

Se mantiene **ASSET_TOOLS_READY=PARTIAL**. El piloto demuestra muestras concretas y un enlace recurso/script, no la recuperación del proyecto original.

API: [UnityPy oficial](https://github.com/K0lb3/UnityPy), contrastada con `ObjectReader.py`, `MeshExporter.py` y `MeshHelper.py` de 1.25.4 instalada. [AssetRipper 2.0.0](https://github.com/AssetRipper/AssetRipper/releases/tag/2.0.0), ayuda y OpenAPI locales conservadas en RUN.
