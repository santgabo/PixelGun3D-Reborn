# Plan 3 — Reimplementación web sin Unity, conservación y single player

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Ejecución directa por defecto; este documento no autoriza delegación, commits ni implementación en la sesión de planificación.

**Goal:** Entregar un cliente de escritorio web sin Unity, servido por HTTP desde Linux headless a la LAN, con menús y mapas conservados, single player funcional y estabilidad/rendimiento comprobados en el navegador del usuario.

**Architecture:** Conversión offline de recursos a GLB + manifiestos JSON; cliente TypeScript/Babylon WebGL 2/Havok con estados, propiedad de recursos y servicios locales explícitos. El servidor solo distribuye archivos, sin renderizado remoto, backend de juego ni conexión a servicios originales.

**Tech Stack:** TypeScript, Babylon.js convencional, Havok WASM, HTML/CSS, glTF 2.0/GLB, Vite, Python, unittest, Vitest, Playwright y http-server para distribución LAN acotada.

**Spec:** [Diseño del Plan 3](../specs/2026-10-10-03-port-web-sin-unity-design.md). Leerlo junto a [investigación tecnológica](../../analysis/tecnologias-port-web.md) y los informes del Plan 2.

**Estado:** DOCUMENTADO; ninguna tarea de implementación ejecutada. El usuario aprobó el stack y solicitó exclusivamente documentación en esta sesión. Los criterios detallados son propuestas explícitas para revisión; no presentar las futuras verificaciones como realizadas.

**Actualización 2026-10-11:** incorpora la [recuperación y pruebas ampliadas del Plan 2](../../analysis/continuacion-plan-2-2026-10-11.md). Esta revisión modifica la planificación; no inicia el port.

## Base recuperada que consume este plan

`RUN = ./.lab/runs/20261011T174958Z-completion/`, relativo a la raíz del checkout que conserva esas salidas privadas. En otro checkout, proporcionar esa ubicación al ejecutar; no copiar una ruta absoluta de esta máquina.

| Entrada bajo `RUN` | Uso en el port |
|---|---|
| `managed/rebuild/`, solución `RecoveredScripts.slnx` | Referencia C# con ajustes contrastados con IL: cuatro proyectos, 1.982 fuentes, compilación conjunta sin errores. `Assembly-CSharp/` contiene la lógica principal. |
| `managed/<ensamblado>/project/` y `managed/<ensamblado>/il/` | Export original e IL para contrastar una representación ambigua; no ejecutar ni distribuir las DLL recuperadas. |
| `staging/Data/` | Datos Unity ya reensamblados; mantenerlos de solo lectura. |
| `resources-final/inventory-final-refined.jsonl` y `refined-summary.json` | Inventario completo de 8.165 archivos/490.030 objetos; campos recuperados de 490.022. Fuente de identidad y valores serializados. |
| `resources-final/unresolved-refined.json` y `raw-unresolved/` | Ocho objetos y sus bytes originales pendientes de interpretación. |
| `assetripper-primary-content/` y `assetripper-unity-project/ExportedProject/` | Medios y representación de escenas ya exportados; reutilizar lo trazable al objeto fuente, sin asumir equivalencia de todo el proyecto Unity. |
| `shader-references-expanded/` | Referencias ShaderLab/GLES recuperadas; requieren adaptación al renderer web. |
| `reports/runtime-results.json` y `runtime/` | Evidencia del APK original: tutorial/menú repetidos en dos instalaciones limpias; Farm probado con perfil derivado. No certifica el cliente web ni todos los mapas. |

El proyecto Unity exportado no se compiló ni ejecutó. Eso no es un prerrequisito del port sin Unity. Las advertencias de layout de AssetRipper en `BulletStackController`/`InputField` requieren contrastar valores con los campos recuperados, no asumir que todo el YAML es fiel. Las validaciones de medios existentes certifican formato; las pruebas de fidelidad, integración y gameplay del cliente web siguen pendientes.

### Tratamiento de los ocho objetos pendientes

- Siete apuntan a clases `FyberEditor` de complementos/configuración del Editor; el octavo referencia `Assembly-CSharp.dll::LpOwerride`. Sus definiciones no aparecen en las 27 DLL suministradas; se conservan 332 bytes personalizados sin interpretar.
- En tarea 1, registrar los ocho por `SourceRef`, clase, ensamblado, bytes opacos, referencias a escenas y decisión sustentada. No excluir por nombre, tamaño o la suposición de que pertenecen a publicidad.
- Una dependencia demostrada de Editor o de un servicio excluido puede quedar fuera del runtime web, conservando su registro y evidencia. `LpOwerride` empieza sin clasificar; no atribuirle una función sin evidencia.
- Si un objeto afecta una función o dato requerido por una escena en alcance, esa escena queda bloqueada hasta recuperar su definición o reconstruir el campo/comportamiento con evidencia. Procesar contenido independiente mientras tanto; no eliminar el mapa ni inventar valores.

## Global Constraints

- Reimplementación completamente sin Unity Editor, runtime Unity, Unity WebGL, emulación/streaming Android o renderizado remoto.
- Navegadores de escritorio; móviles fuera de esta iteración.
- No se repiten pruebas de integridad del Plan 2. Su documentación es la línea base aceptada. No se recalculan hashes de originales, comparan APK/OBB, repiten preflights ni reejecuta el original como requisito de este plan.
- No volver a decompilar todos los ensamblados, inventariar los 8.165 archivos ni repetir las validaciones estructurales de medios. Consumir las salidas anteriores; hacer lecturas/conversiones dirigidas y pruebas nuevas cuando las necesite el port.
- Los originales y salidas del Plan 2 permanecen de solo lectura. Las nuevas conversiones van a `./.lab/web-port/`; los datos derivados del juego y capturas no se publican automáticamente en Git.
- No usar `./tools/prepare_unity_data.py` como preflight: vuelve a comprobar entradas. Consumir el staging ya realizado. Si no está disponible, pedir ubicación/recuperación, no repetir el Plan 2.
- WebGL 2 y WASM/SIMD son capacidades requeridas; ausencia produce pantalla explicativa. HTTP LAN no es contexto seguro como localhost.
- No depender de WebGPU, service workers, HTTPS, memoria compartida ni flags especiales.
- Todos los WASM, fuentes y decodificadores se alojan localmente. La distribución no debe emitir peticiones a CDN, endpoints originales o telemetría.
- No omitir mapas o rutas problemáticos para declarar el port completo. El primer mapa funcional es un hito intermedio, no el entregable final.
- No cambiar firewall, permisos administrativos, routing ni certificados automáticamente.
- No iniciar implementación, instalar dependencias del juego o abrir servicios en esta sesión. En una sesión futura, confirmar autorización de ejecución; no crear commits/push ni subagentes sin autorización.

## Review Focus

1. Cancelar A y pedir B durante una carga lenta: A no reaparece ni retiene física/audio — tarea 5.
2. Transformaciones anidadas, espejo y colliders desalineados: el mapa conserva geometría y espacio jugable — tareas 3–4.
3. Escape, foco perdido y pestaña suspendida: no quedan teclas retenidas ni simulación acumulada — tareas 7–8.
4. Guardado denegado, corrupto o futuro: juego local utilizable sin destruir el progreso recuperable — tarea 6.
5. HTTP a IP LAN con binario ausente o decoder en CDN: error recuperable, cero dependencia accidental de localhost/Internet — tareas 2, 5 y 13.

---

## Organización de trabajo y puertas

| Etapa | Tareas | Entregable / puerta |
|---|---|---|
| Contratos y cliente mínimo | 1–2 | G0: entradas existentes localizadas, catálogo inicial y shell web |
| Conservación y navegación | 3–6 | G1: menú y primer mapa original por HTTP LAN |
| Single player vertical | 7–9 | G2: jugar, daño/objetivo, morir/reiniciar y salir |
| Cobertura y robustez | 10–11 | G3: contenido en alcance, sin mapas omitidos |
| Rendimiento y entrega | 12–14 | G4: matriz de aceptación y manual LAN |

Ejecutar secuencialmente. Las tareas 3–4 procesan primero dependencias del mapa vertical; la tarea 10 repite la misma ruta por lotes para cubrir el resto. Las tareas 7–9 implementan primero los comportamientos de ese recorrido; la 10 completa las familias de comportamientos restantes. No desarrollar sistemas online en paralelo.

Si una tarea crece por una familia de contenido no soportada, añadir subtareas verificables dentro de su etapa y actualizar cobertura; no saltar el contrato, sustituir contenido ni declarar PASS parcial como global.

## Archivos previstos y responsabilidad

Son rutas futuras; este plan no las crea.

| Ruta | Responsabilidad |
|---|---|
| `./tools/web_port/catalog.py`, `./tools/web_port/contracts.py` | Catálogo y contratos de conversión; procedencia por archivo/path_id |
| `./tools/web_port/unity_reader.py`, `references.py` | Lectura dirigida y resolución de objetos requeridos |
| `./tools/web_port/transforms.py`, `glb_writer.py`, `materials.py` | Conversión visual y espacial |
| `./tools/web_port/animation.py`, `ui_assets.py`, `audio.py`, `navigation.py` | Familias de recursos restantes |
| `./tools/export_web_scene.py` | CLI de conversión de una escena y dependencias |
| `./tests/web_port/` | Pruebas sintéticas del nuevo conversor; no auditoría de originales |
| `./web/package.json`, `package-lock.json`, `.npmrc`, `.node-version` | Toolchain fijada del cliente |
| `./web/index.html`, `vite.config.ts`, `tsconfig.json` | Entrada y build |
| `./web/src/content/{types,validate,repository}.ts` | Contrato web y carga de datos |
| `./web/src/app/{state,controller,capabilities}.ts` | Estados, acciones y soporte de plataforma |
| `./web/src/runtime/{engine,scene-session,resource-scope,clock}.ts` | Motor, propiedad, liberación y tiempo |
| `./web/src/services/{contracts,local-services,save-store}.ts` | Servicios dummy y persistencia |
| `./web/src/ui/`, `./web/src/input/`, `./web/src/audio/` | Menús/HUD, controles y sonido |
| `./web/src/gameplay/` | Jugador, armas, daño, enemigos, objetivos y navegación |
| `./web/src/diagnostics/` | Contadores, timings y exportación de diagnóstico |
| `./web/scripts/{publish-content,serve-lan}.mjs` | Publicación por allowlist y servidor de `dist` |
| `./web/tests/{fixtures,e2e}/`, `./web/playwright.config.ts` | Recursos propios sintéticos y pruebas de navegador |
| `./.lab/web-port/` | Catálogo real, conversiones, perfiles, capturas e informes privados |
| `./docs/web/` | Toolchain, cobertura saneada, decisiones y uso |

Tests unitarios TS junto al módulo: `*.test.ts`. No mezclar binarios recuperados en fixtures versionados. Ampliar `.gitignore` para `./.lab/web-port/`, `./web/dist/`, recursos derivados de publicación, `./web/test-results/` y `./web/playwright-report/`; conservar únicamente fixtures originales propios.

## Contratos comunes que deben existir antes de consumidores

Definir en tarea 1 (Python) y tarea 2 (TS), con fixtures JSON compartidos y pruebas de conformidad:

- `SourceRef = { file: string, pathId: string }`: path_id decimal como **string** para evitar pérdida de precisión JS.
- `SceneKind = 'bootstrap' | 'menu' | 'single-player' | 'multiplayer-map' | 'other'`.
- `CoverageStatus = 'pending' | 'converted' | 'functional' | 'accepted' | 'blocked'`: estado del contenido, distinto del PASS/PARTIAL global.
- `ContentCatalog = { schemaVersion: 1, releaseId: string, scenes: SceneEntry[] }`.
- `SceneEntry = { id: string, source: SourceRef, kind: SceneKind, modeIds: string[], manifestUrl: string | null, status: CoverageStatus, blockers: string[] }`.
- `SceneManifest = { schemaVersion: 1, id: string, basis: 'RH_Y_UP_METERS', visualPackages: AssetRef[], nodes: NodeSpec[], colliders: ColliderSpec[], spawns: SpawnSpec[], triggers: TriggerSpec[], lighting: LightingSpec, audio: AudioSpec[], gameplay: GameplaySpec }`.
- `AssetRef = { id: string, url: string, required: boolean }`; rutas locales relativas, sin `..`, esquemas externos ni salida de raíz.
- `NodeSpec`: id estable, SourceRef, parentId nullable, transform local TRS y enlace explícito al nodo GLB. Identidad por índice/metadata, no por nombre visible.
- `ColliderSpec`: nodo y pose, forma discriminada box/sphere/capsule/mesh, dimensiones, grupos, trigger; mallas estáticas separadas de cuerpos dinámicos.
- `SpawnSpec`: id, rol player/enemy/explore y pose. `TriggerSpec`: volumen, evento y objetivo. Sin `any` ni ejecución de strings de código.
- `LightingSpec`: ambiente/luces/skybox/lightmaps con UV y transforms explícitos. `AudioSpec`: recurso, espacialidad, volumen y loop.
- `GameplaySpec`: modeId nullable y referencias locales a configuraciones de jugador/armas/enemigos/objetivos/navegación; las estructuras se completan en tareas 7–9 con fixtures y versión de esquema explícita si cambia el contrato.
- `LocalProfile = { schemaVersion: 1, settings: Settings, progress: Progress }`; `Settings` define audio, sensibilidad y calidad; `Progress` define completados/desbloqueos solo locales con identificadores del catálogo.

No inventar datos ausentes para satisfacer el esquema: un componente crítico no traducido bloquea esa escena, salvo entrada catalogada explícitamente como no jugable.

---

### Tarea 1 — Localizar salidas existentes y fijar catálogo funcional

**Files:** crear `./tools/web_port/{__init__,contracts,catalog}.py`, `./tests/web_port/test_catalog.py`, `./docs/web/content-scope.md`; datos reales en `./.lab/web-port/catalog/`, incluido `opaque-components.json`.

**Interfaces:** consume las entradas de la base recuperada. Produce `build_catalog(build_settings: dict, evidence: dict) -> dict` y catálogo schemaVersion 1; `SourceRef` y categorías anteriores. `opaque-components.json` contiene `{ schemaVersion: 1, components: OpaqueComponent[] }`; cada registro usa `{ source: SourceRef, assembly: string, type: string, opaqueBytes: number, decision: 'pending' | 'excluded' | 'blocked' | 'resolved', affectedSceneIds: string[], reason: string, evidence: string[] }`. `pending` conserva impacto desconocido; `blocked` identifica una dependencia requerida aún ilegible; `resolved` requiere evidencia de recuperación/traducción validada. Una lista vacía de escenas no basta para demostrar exclusión.

- [ ] Registrar las rutas de la base recuperada, sin hashes ni reejecución de staging. Si `./.lab/runs` no está aquí, localizar por rutas proporcionadas; no recorrer/revalidar todos los originales.
- [ ] Escribir `test_catalog_preserves_all_scene_entries`, `test_path_id_is_decimal_string`, `test_duplicate_names_keep_distinct_ids`, `test_unknown_scene_is_not_silently_dropped`; comprobar conteo de fixtures, IDs y bloqueo explícito.
- [ ] Añadir fixtures/tests `test_opaque_component_exclusion_keeps_source_and_evidence`, `test_required_opaque_component_blocks_affected_scene`, `test_unknown_component_is_not_excluded_by_name`; conservar registro, impedir exclusión sin evidencia y no bloquear escenas independientes.
- [ ] Ejecutar `python3 -m unittest discover -s ./tests/web_port -p 'test_catalog.py' -v`: RED por funcionalidad ausente.
- [ ] Implementar catálogo a partir de BuildSettings/evidencia; clasificar escenas leyendo únicamente lo necesario. Definir mapa vertical como el tutorial original documentado, una vez resuelto su ID, y añadir la ruta de menú local hacia él.
- [ ] Repetir comando: GREEN. Producir catálogo real y mapa de referencias `ensamblado/tipo/método ↔ componente ↔ escena` usando lo ya recuperado.
- [ ] Registrar los ocho objetos en `opaque-components.json` y seguir sus referencias de forma dirigida. Documentar decisiones justificadas y bloqueos por escena; dejar pendientes las funciones todavía desconocidas.
- [ ] Escribir `content-scope.md`: todas las entradas, rutas locales, modos single player, mapas multiplayer para exploración y bloqueos. Si no se identifica aún un menú o modo, marcarlo pendiente; no inferirlo del nombre del archivo.

**Aceptación:** ninguna escena desaparece del catálogo; el alcance y mapa vertical tienen identificadores reales. Los ocho objetos tienen registro y decisión/evidencia o pendiente explícito. No se ha repetido ninguna comprobación de integridad.

### Tarea 2 — Shell web, contratos TS y HTTP LAN mínimo

**Files:** crear configuración `./web/`, `./web/src/{main,content/types,content/validate,app/capabilities}.ts`, `./web/scripts/serve-lan.mjs`, tests correspondientes, `./web/tests/e2e/bootstrap.spec.ts`, `./docs/web/toolchain.md`; modificar `.gitignore`.

**Interfaces:** `validateCatalog(value: unknown): ContentCatalog`, `validateManifest(value: unknown): SceneManifest`; `detectCapabilities(canvas: HTMLCanvasElement): Promise<CapabilityReport>` devuelve WebGL2, WASM/SIMD y causas de falta de soporte. CLI `npm run serve:lan -- --host <IP> --port <port>` sirve solamente `./web/dist/`.

- [ ] Elegir versiones estables compatibles consultando docs de esas versiones; fijar Node/npm y paquetes exactos en `.node-version`, package.json, `.npmrc` y lockfile. Incluir Babylon core/loaders, Havok, TypeScript, Vite, Vitest, Playwright y http-server. No sustituir Babylon convencional por Lite.
- [ ] Crear scripts `build`, `typecheck`, `test:unit`, `test:e2e`, `publish:content`, `serve:lan`; `build` compila TS/Vite sin publicar todo `.lab`.
- [ ] Escribir tests de esquema compartido Python/TS, versión futura, path_id grande, URL externa, capacidades ausentes y WebGPU ausente con WebGL2 presente. Escribir smoke navegador: pantalla inicial visible y ningún request externo.
- [ ] Ejecutar `cd ./web && npm run test:unit`: RED por validadores/capabilities ausentes. No contar un error de instalación como RED válido.
- [ ] Implementar validadores, shell accesible y error de soporte. Crear solo un fixture gráfico propio; no presentarlo como primer mapa recuperado.
- [ ] Implementar wrapper de http-server: raíz `./web/dist` relativa al repositorio (resolverla desde la ubicación del wrapper al ejecutar), host requerido, puerto 8080 por defecto, sin listar directorios, sin dotfiles, sin proxy ni fallback HTML de assets. Rechazar arranque si no existe build; sin cambios de firewall.
- [ ] Ejecutar `npm run typecheck && npm run test:unit && npm run build && npm run test:e2e -- ./tests/e2e/bootstrap.spec.ts`: GREEN en navegadores disponibles; registrar faltantes como NOT_RUN.
- [ ] Documentar URL HTTP LAN y demostrar acceso desde la MacBook cuando esté disponible. No convertir éxito de localhost en acceso LAN comprobado.

**Aceptación:** shell visible por HTTP sin WebGPU ni conexión externa; toolchain fijada. G0 no certifica aún mapas o gameplay.

### Tarea 3 — Conversión de escena estática y mapa original

**Files:** crear `./tools/web_port/{unity_reader,references,transforms,glb_writer,materials}.py`, `./tools/export_web_scene.py`, `./tests/web_port/test_static_scene.py`.

**Interfaces:** `read_scene(data_root: Path, scene_ref: dict, *, recovery_root: Path) -> dict`; `convert_scene(scene: dict, output: Path) -> dict` produce SceneManifest; CLI `python3 ./tools/export_web_scene.py --data-root "$DATA" --recovery-root "$RUN" --catalog "$CATALOG" --scene "$SCENE_ID" --output "$OUT"`. DATA es staging ya existente, RUN la raíz de recuperación indicada arriba; output nuevo fuera de entradas. El reader consume desde recovery_root los campos refinados y la identidad fuente de los recursos reutilizados.

- [ ] Escribir fixtures propios: jerarquía padre/hijo con escala negativa, triángulo asimétrico, UV/normal/tangente, IDs repetidos entre archivos, referencias compartidas y collider desplazado.
- [ ] Escribir tests que comparen coordenadas finales esperadas, winding, índices, materiales y pose del collider; fixture con campo crítico ausente debe producir bloqueo, no mapa vacío.
- [ ] Ejecutar `python3 -m unittest discover -s ./tests/web_port -p 'test_static_scene.py' -v`: RED.
- [ ] Implementar resolución por archivo/path_id, conversión a RH/Y-up/metros y GLB + manifiesto. Usar el inventario refinado y las herramientas ya instaladas, incluido TypeTreeGeneratorAPI; resolver layouts solo de tipos necesarios para esta conversión, sin reabrir la recuperación global.
- [ ] Reutilizar medios de PrimaryContent cuando se conserve su vínculo con `SourceRef`, parámetros y base de coordenadas; evitar una segunda conversión de ejes. Completar jerarquías, colliders y gameplay en el manifiesto: un GLB válido no contiene por sí solo todo el mapa.
- [ ] Traducir materiales/UV/lightmaps explícitamente; no perder iluminación horneada por una conversión PBR por defecto. Conservar referencias de procedencia sin regenerar hashes.
- [ ] Contrastar `BulletStackController`/`InputField` con los campos recuperados cuando sean dependencias del contenido elegido; usar las referencias de shaders expandidas para adaptar materiales. No aceptar YAML o GLSL enviado por el export como proyecto/runtime ya compilable.
- [ ] Repetir tests: GREEN. Ejecutar conversión del mapa vertical y sus dependencias, no exportación masiva del archivo completo.
- [ ] Emitir diagnóstico por componente no soportado, con fuente y efecto visual/jugable. Corregir lo crítico antes de aceptar el mapa.

**Aceptación:** mapa original convertible con transforms, materiales y colisiones alineados. La lectura/exportación nueva no se presenta como una nueva certificación de integridad del Plan 2.

### Tarea 4 — Animaciones, audio y recursos de interfaz

**Files:** crear `./tools/web_port/{animation,ui_assets,audio}.py`, `./tests/web_port/test_media_conversion.py`; ampliar `glb_writer.py` y CLI de tarea 3 con estas familias.

**Interfaces:** `convert_animation(data: dict) -> dict`, `export_ui_assets(data: dict, output: Path) -> dict`, `export_audio(data: dict, output: Path) -> dict`; producen recursos locales y referencias consumibles por SceneManifest y UI.

- [ ] Escribir fixtures: esqueleto de dos huesos con bind poses, clip con keyframes conocidos, atlas con recorte/pivote/9-slice y PCM corto con loop. Comprobar poses interpoladas, duración, UV/pivote y parámetros de audio.
- [ ] Ejecutar `python3 -m unittest discover -s ./tests/web_port -p 'test_media_conversion.py' -v`: RED.
- [ ] Implementar conversión de skins/clips, sprites/fuentes y audio a formatos soportados por los navegadores objetivo. Preservar parámetros y nombres para presentación, no usarlos como IDs únicos.
- [ ] Repetir tests: GREEN; convertir solo lo necesario para menú, jugador/arma/enemigo vertical y sonido correspondiente.
- [ ] Registrar faltantes de shaders, animaciones o UI como bloqueos/fidelidad parcial, nunca sustituirlos por assets inventados sin decisión explícita.

**Aceptación:** recursos animados/UI/audio de la sección vertical disponibles; reproducción perceptual se acepta con el runtime en tareas posteriores, no por mera existencia de archivos.

### Tarea 5 — Carga de escenas, propiedad y recuperación

**Files:** crear `./web/src/content/repository.ts`, `./web/src/runtime/{engine,scene-session,resource-scope}.ts`, `./web/src/app/{state,controller}.ts`, `./web/scripts/publish-content.mjs`, `./web/scripts/publish-content.test.ts`, unit tests y `./web/tests/e2e/scene-loading.spec.ts`.

**Interfaces:** `ContentRepository.loadScene(id: string, signal: AbortSignal): Promise<SceneManifest>`; `createSceneSession(manifest: SceneManifest, services: RuntimeServices, signal: AbortSignal): Promise<SceneSession>`. `SceneSession` expone `update(dt: number): void`, `pause(): void`, `resume(): void`, `dispose(): void`. `RuntimeServices` contiene engine, repositorio y diagnósticos; servicios locales se añaden por contrato en tarea 6.

- [ ] Escribir tests A→B con A lento, cancelación, dispose doble, recurso 404, manifiesto incompatible, decoder externo y descarga fallida de Havok. A nunca se activa después de B; cada recurso propio termina liberado exactamente una vez.
- [ ] Ejecutar `cd ./web && npm run test:unit -- ./src/runtime ./src/content ./src/app`: RED.
- [ ] Implementar Babylon Engine WebGL2, escena dextrógira, carga por paquetes y contenedor, resolución local de WASM/decoders, estados definidos en spec y un solo render loop.
- [ ] Implementar gestión explícita de recursos compartidos y eliminación de resultados obsoletos incluso cuando la API subyacente no cancele realmente la descarga.
- [ ] Escribir RED→GREEN del publicador mínimo con la firma de tarea 13: copiar únicamente catálogo/manifiestos y sus recursos permitidos a `dist/content/<release>/`, rechazar escapes/symlinks y no activar publicación incompleta. Usarlo después de cada build para probar mapas reales desde G1; tarea 13 completa endurecimiento y manual.
- [ ] Repetir unit tests: GREEN; ejecutar `npm run test:e2e -- ./tests/e2e/scene-loading.spec.ts` con recursos sintéticos y errores inyectados.
- [ ] Cargar mapa original con una cámara de inspección, contrastar puntos de vista, geometría, luz y colisiones; conservar diferencias y capturas privadas. Esta cámara es de diagnóstico, no el controlador final.

**Aceptación:** mapa visible; volver al menú tras fallo; sin requests externos, escenas huérfanas ni promesa de fidelidad basada únicamente en test sintético.

### Tarea 6 — Servicios dummy, guardado y menús principales

**Files:** crear `./web/src/services/{contracts,local-services,save-store}.ts`, `./web/src/ui/{menu,hud}.ts`, `./web/src/ui/styles.css`, unit tests y `./web/tests/e2e/menu.spec.ts`.

**Interfaces:** `GameServices = { loadProfile(): Promise<ProfileLoadResult>; saveProfile(profile: LocalProfile): Promise<SaveResult>; onlineAvailability(): 'unavailable' }`; `ProfileLoadResult = { profile: LocalProfile; temporary: boolean; warning?: 'denied' | 'corrupt' | 'future-version' }`; `SaveResult = { persisted: boolean; reason?: 'denied' | 'quota' | 'corrupt' | 'future-version' }`. `mountMenu(root: HTMLElement, model: MenuModel, dispatch: (action: AppAction) => void): () => void` devuelve liberador. `MenuModel` deriva catálogo/perfil/errores; AppAction es unión de acciones de estado sin comandos de motor.

- [ ] Escribir tests de perfil ausente, JSON corrupto, versión futura, almacenamiento denegado/cuota; seguir jugando en memoria y no sobrescribir silenciosamente datos recuperables.
- [ ] Escribir tests de navegación teclado/ratón, selección de mapa, volver atrás, ajustes y botón online deshabilitado. El shell no espera login ni servicios antiguos.
- [ ] Añadir tests con perfiles sintéticos nuevo y con tutorial local completado: el menú permite la ruta a Campaign según progreso local, sin esperar una primera partida multijugador ni emitir peticiones externas. No importar el fixture Android ni fabricar un `FirstMatchCompleted` online; el recorrido jugable real se verifica tras tareas 9–10.
- [ ] Ejecutar `cd ./web && npm run test:unit -- ./src/services ./src/ui`: RED.
- [ ] Implementar servicios y almacenamiento local; aislar errores de persistencia. No incorporar Photon, SDK publicitario ni emulador genérico de backend.
- [ ] Reconstruir menú/HUD inicial con sprites, tipografía, anclajes y disposición originales; estilos escalables sin rediseño. Conectar estados y carga de tarea 5.
- [ ] Repetir unit tests y `npm run test:e2e -- ./tests/e2e/menu.spec.ts`: GREEN; revisar menú → mapa → menú desde MacBook por HTTP.

**Aceptación G1:** carga de menú y primer mapa original por LAN, con servicios dummy no bloqueantes. Exploración aún no equivale a single player completo.

### Tarea 7 — Tiempo, input, movimiento y física

**Files:** crear `./web/src/runtime/clock.ts`, `./web/src/input/{keyboard-mouse,pointer-lock}.ts`, `./web/src/gameplay/{player-config,player-controller,physics-world}.ts`, tests y `./web/tests/e2e/movement.spec.ts`.

**Interfaces:** `FixedClock.advance(seconds: number, step: (dt: number) => void): void`, `reset(): void`; `PlayerController.tick(input: PlayerInput, dt: number): PlayerSnapshot`; `PlayerInput` define ejes, mirar, salto y acciones; `PlayerSnapshot` contiene pose, velocidad y soporte. `createPhysicsWorld(session: SceneSession): PhysicsWorldHandle` encapsula Havok y libera cuerpos/controlador.

- [ ] Extraer configuración y referencias de `FirstPersonControlSharp`/`Player_move_c` necesarias; registrar fuente de velocidad, FOV, gravedad, salto y estados especiales, sin copiar enteras las DLL al cliente.
- [ ] Escribir tests de 60 Hz y máximo 5 pasos/frame, reset tras pausa, tecla retenida al perder foco, rechazo de pointer lock y Escape.
- [ ] Escribir recorridos sintéticos: pared, pendiente, escalón, esquina, techo, caída y plataforma si la escena la exige. Comprobar no atravesar sólidos y alineación con la geometría.
- [ ] Ejecutar `cd ./web && npm run test:unit -- ./src/runtime/clock.test.ts ./src/input ./src/gameplay`: RED.
- [ ] Implementar controlador Havok con configuración del juego, input relativo y pausa automática; no ligar velocidad a fps. Recuperar foco exige acción explícita de reanudación.
- [ ] Repetir tests y `npm run test:e2e -- ./tests/e2e/movement.spec.ts`: GREEN; calibrar recorridos del mapa vertical y documentar diferencias conocidas.

**Aceptación:** jugador recorre mapa real sin atravesar paredes ni acumular simulación al volver a la pestaña. Controles funcionales en MacBook.

### Tarea 8 — Armas, daño, muerte y reinicio

**Files:** crear `./web/src/gameplay/{weapon-config,weapons,damage,player-life}.ts`, `./web/src/ui/weapon-hud.ts`, tests y `./web/tests/e2e/combat.spec.ts`.

**Interfaces:** `WeaponSystem.tick(input: WeaponInput, dt: number): readonly ShotEvent[]`; `DamageSystem.apply(event: DamageEvent): LifeState`; `PlayerLife.reset(spawn: SpawnSpec): PlayerSnapshot`. El reinicio completo usa la transición de carga del controlador de tarea 5, no depende de LocalGame aún no creado. Config discriminada de arma hitscan/proyectil/melee según comportamiento documentado; no convertir todas a hitscan.

- [ ] Registrar parámetros del arma inicial y sus fuentes en `WeaponManager`/`WeaponSounds`; ampliar contratos de gameplay con munición, daño, cadencia, recarga y efectos necesarios.
- [ ] Escribir tests de disparo bloqueado durante pausa/carga/muerte, cadencia en paso fijo, munición cero, recarga y límites, impacto bloqueado por pared, muerte una vez y reinicio limpio.
- [ ] Ejecutar `cd ./web && npm run test:unit -- ./src/gameplay`: RED.
- [ ] Implementar primera familia de arma real, daño, feedback visual/HUD y reinicio sin duplicar escena, listeners o física.
- [ ] Repetir tests y `npm run test:e2e -- ./tests/e2e/combat.spec.ts`: GREEN; verificar el arma/modelo/animación reales en la escena.

**Aceptación:** combate local básico reproducible; no basta un raycast de diagnóstico o un contador falso de munición.

### Tarea 9 — Enemigos, objetivos y sección vertical completa

**Files:** crear `./web/src/gameplay/{enemy-config,enemies,navigation,objectives,local-game}.ts`, `./tools/web_port/navigation.py`, pruebas asociadas, `./web/tests/e2e/single-player.spec.ts`, `./docs/web/behavior-map.md`.

**Interfaces:** `Navigation.findPath(from: Vec3, to: Vec3): readonly Vec3[] | null`; `EnemySystem.tick(dt: number, player: PlayerSnapshot): readonly GameEvent[]`; `Objectives.consume(event: GameEvent): ObjectiveState`; `createLocalGame(session: SceneSession, profile: LocalProfile): LocalGame` conecta tareas 7–8 y expone tick/pause/resume/restart/dispose.

- [ ] Especificar estados/enemigos/objetivos del modo vertical usando código/datos existentes; registrar cada transición y parámetro en behavior-map, no inventar IA para suplir información no leída.
- [ ] Contrastar la entrada al portal con `GotToNextLevel.Update`: el original comprueba distancia 3D al jugador (`SqrMagnitude < 2.25`), no basta asumir un evento de collider. Usar la evidencia de tutorial como referencia del original; Farm con perfil derivado no prueba el desbloqueo natural ni completar ese nivel.
- [ ] Escribir tests de detección/ataque/muerte, camino sin ruta, paredes y obstáculos, objetivo cumplido solo una vez, tutorial/progreso y salida al resultado/menú.
- [ ] Añadir `test_portal_requires_3d_distance_below_1_5m`: igualdad y separación vertical mayor que 1,5 m no completan el objetivo; proximidad menor sí lo completa una sola vez, conforme al método fuente.
- [ ] Ejecutar `python3 -m unittest discover -s ./tests/web_port -p 'test_navigation.py' -v` y `cd ./web && npm run test:unit -- ./src/gameplay`: RED.
- [ ] Implementar navegación a partir de datos portables; si no sirven, generar grafo/navmesh offline desde superficie transitable y colisiones. Registrar algoritmo/dependencia antes de añadirlo y comprobarlo con fixtures; no usar movimiento directo a través de paredes.
- [ ] Implementar reglas del modo, enemigos y objetivos, conectando guardado local únicamente tras eventos de progreso válidos.
- [ ] Repetir tests: GREEN; `npm run test:e2e -- ./tests/e2e/single-player.spec.ts` cubre menú → mapa → jugar → daño → muerte/reinicio → completar objetivo → resultado → menú.

**Aceptación G2:** sección vertical jugable, no solo mapa exploratorio; valores contrastados con fuentes y desviaciones explícitas.

### Tarea 10 — Ampliar cobertura a escenas, mapas y modos restantes

**Files:** ampliar conversores y gameplay de familias que lo requieran; crear `./web/src/ui/{results,settings,content-selector}.ts`, `./web/tests/e2e/content-coverage.spec.ts`, `./tests/web_port/test_coverage.py`; actualizar `./docs/web/{content-scope,behavior-map}.md`.

**Interfaces:** `buildCoverageReport(catalog: ContentCatalog, results: SceneResult[]): CoverageReport` en `./web/src/diagnostics/coverage.ts`; SceneResult incluye sceneId, navegación, carga, fidelidad, gameplay y bloqueos. Exploration usa modeId explícito y no atribuye reglas multiplayer implementadas.

- [ ] Escribir test de cobertura: toda entrada de catálogo aparece exactamente una vez; faltar un mapa o convertirlo sin recorrido no permite estado accepted.
- [ ] Ejecutar `python3 -m unittest discover -s ./tests/web_port -p 'test_coverage.py' -v` y `cd ./web && npm run test:unit -- ./src/diagnostics/coverage.test.ts`: RED; implementar reporte con totales por categoría y razones para no jugables.
- [ ] Procesar lotes empezando por menús/rutas locales y mapas single player, luego mapas multiplayer para exploración. Para cada familia ausente, escribir fixture/test RED antes del conversor o comportamiento GREEN.
- [ ] Actualizar `opaque-components.json` y los bloqueos al ampliar dependencias. Un objeto excluido conserva su motivo; un objeto requerido sigue bloqueando las escenas afectadas hasta resolverse. No declarar cobertura completa con una función desconocida que pueda afectar contenido en alcance.
- [ ] Añadir armas, enemigos, triggers, plataformas, materiales y animaciones que cada modo requiera. Reutilizar sistemas; no introducir excepciones por nombre de mapa sin fuente.
- [ ] Completar menús, resultados, ajustes, transiciones y guardado de cada recorrido; pantallas online indican indisponibilidad sin llamadas externas.
- [ ] Ejecutar `cd ./web && npm run test:e2e -- ./tests/e2e/content-coverage.spec.ts`; el fixture de catálogo selecciona todos los mapas convertidos y recorre las rutas definidas. Un mapa bloqueado debe aparecer como fallo/bloqueo, no filtrarse para que la suite pase.
- [ ] Incluir en ese recorrido un perfil local nuevo: tutorial → menú → Campaign → primer nivel convertido → menú, sin fixture Android, primera partida online ni peticiones externas.
- [ ] Revisar fidelidad de cada mapa y menús desde vistas definidas, conservando capturas privadas y resúmenes saneados. Mantener PARTIAL si falta referencia o función esencial.

**Aceptación G3:** catálogo cubierto; ningún mapa perdido silenciosamente. Modos single player completos dentro de su cobertura, mapas online conservados en exploración explícita.

### Tarea 11 — Audio, recuperación y pruebas prolongadas de ciclo de vida

**Files:** crear `./web/src/audio/audio-manager.ts`, `./web/src/runtime/context-recovery.ts`, `./web/src/diagnostics/resource-counts.ts`, tests y `./web/tests/e2e/{recovery,lifecycle}.spec.ts`.

**Interfaces:** `AudioManager.unlock(): Promise<void>`, `pause(): void`, `dispose(): void`; `ResourceCounts.snapshot(): ResourceSnapshot` cuenta sesiones, cuerpos, texturas propias, listeners y sonidos, separando caché compartida intencional.

- [ ] Escribir tests de autoplay rechazado, sonido cancelado al salir, context loss durante carga/juego, recuperación fallida con retorno al menú y ausencia de doble liberación.
- [ ] Escribir recorrido de 30 ciclos con reinicio/pausa/cambio de mapa; tras warmup, contadores de recursos exclusivos vuelven al valor base y recursos compartidos permanecen dentro de su cota declarada.
- [ ] Ejecutar `cd ./web && npm run test:unit -- ./src/audio ./src/runtime ./src/diagnostics`: RED.
- [ ] Implementar audio espacial, loops/volúmenes, desbloqueo por gesto y recuperación; completar limpieza y cancelación de todas las familias añadidas en tarea 10.
- [ ] Repetir unit tests y `npm run test:e2e -- ./tests/e2e/recovery.spec.ts ./tests/e2e/lifecycle.spec.ts`: GREEN.
- [ ] Realizar sesión de 60 minutos y registrar crashes, bloqueos, pérdida de input y tendencia de memoria/recursos; corregir con repro/test de cada fallo antes de repetir.

**Aceptación:** cero fallos no controlados en los recorridos, sin crecimiento acumulativo de recursos vivos. Si heap no es observable, indicarlo; no inventar mediciones.

### Tarea 12 — Presupuestos y optimización medida

**Files:** crear `./web/src/diagnostics/{frame-metrics,load-metrics,report}.ts`, tests, `./docs/web/performance.md`; optimizar únicamente módulos que aparezcan en perfiles.

**Interfaces:** `FrameMetrics.record(deltaMs: number, active: boolean): void`, `summarize(): FrameSummary`; `LoadMetrics` separa navegación→menú y selección→jugable, frío/caliente; `exportDiagnostics(): Blob` permite descargar resultados locales sin telemetría.

- [ ] Escribir tests de percentiles con secuencias conocidas, exclusión de pausa/carga, medición fría/caliente y contadores; ejecutar `cd ./web && npm run test:unit -- ./src/diagnostics`: RED.
- [ ] Implementar medición, límite inicial de resolución interna 1920×1080 y ajustes de calidad explícitos; no forzar DPR Retina completo ni ocultar una caída de resolución en el informe.
- [ ] Repetir tests: GREEN. Registrar equipo/macOS/navegador, energía, resolución y LAN antes de medir; si no están disponibles, documentar NOT_RUN.
- [ ] Medir 5 minutos activos tras 30 s de calentamiento: mediana ≤17,5 ms, p95 ≤25 ms, p99 ≤50 ms; registrar pausas >100 ms. Menú frío ≤5 s; mapa frío ≤10 s/caliente ≤5 s como presupuestos iniciales de spec.
- [ ] Priorizar causa medida: draw calls, texturas, colisiones, asignaciones/GC, animación, carga o compilación de shaders. Aplicar batching/instancias/culling/compresión por lote manteniendo identidades y fidelidad.
- [ ] Repetir vistas funcionales y mediciones tras cada cambio; no aceptar una optimización que pierda mapas, materiales o gameplay. Si un presupuesto resulta inviable, pedir ajuste documentado, no relajar umbrales en secreto.

**Aceptación:** resultados reales de MacBook y límites conocidos, sin extrapolar benchmarks de Linux/software renderer a GPU del usuario.

### Tarea 13 — Publicación estática autocontenida y manual LAN

**Files:** ampliar `./web/scripts/publish-content.mjs` y `publish-content.test.ts` de tarea 5; crear `./web/tests/e2e/deployment.spec.ts`, `./docs/web/{run-lan,troubleshooting}.md`; completar `serve-lan.mjs` de tarea 2.

**Interfaces:** CLI `npm run publish:content -- --source <CONTENT_DIR> --release <RELEASE_ID>` copia solo recursos del catálogo/manifiestos a `./web/dist/content/<release>/`; fija el catálogo de entrada de esa publicación. `serve:lan` conserva firma tarea 2.

- [ ] Escribir tests de allowlist, path traversal/symlink, recurso crítico ausente, binario 404, tipos MIME WASM/JS/audio, ausencia de listado, y publicación sin `.lab`, DLL, originales, secretos o sourcemaps de contenido recuperado.
- [ ] Ejecutar `cd ./web && npm run test:unit -- scripts`: RED.
- [ ] Completar publicación local versionada sin hashear originales ni copiar indiscriminadamente carpetas. Una publicación fallida no reemplaza la activa; no mezclar releaseId de manifiestos con paquetes de otra versión. Construir actualizaciones con el servidor detenido o en un directorio independiente antes del cambio; `vite build` puede vaciar `dist`, por lo que no se ejecuta sobre una distribución activa.
- [ ] Configurar dependencias/código para cero recursos externos, incluidos decoders y fuentes. No habilitar proxy/fallback SPA que convierta 404 de WASM en HTML.
- [ ] Ejecutar `npm run typecheck && npm run test:unit && npm run build`; después publicar contenido y `npm run test:e2e -- ./tests/e2e/deployment.spec.ts`: GREEN.
- [ ] Documentar comandos desde `./web/`: `npm ci`, `npm run build`, `npm run publish:content -- --source "$CONTENT_DIR" --release "$RELEASE_ID"`, `npm run serve:lan -- --host "$LAN_IP" --port 8080`; abrir `http://<LAN_IP>:8080/` en MacBook. Vars son rutas/IP/ID del despliegue registradas, no rutas hardcodeadas al worktree vecino.
- [ ] Documentar parada del proceso, actualización/reversión por release y diagnóstico de 404, MIME, WASM/SIMD, WebGL, permisos de audio/input y firewall bloqueado. No recomendar desactivar seguridad.

**Aceptación:** Linux sirve exclusivamente build y contenido autorizado, sin pantalla/GPU, cuentas o Internet durante juego. El acceso LAN se verifica desde otra máquina.

### Tarea 14 — Aceptación, cobertura multiplataforma y cierre

**Files:** crear `./docs/web/acceptance.md`, `./docs/analysis/resultado-plan-3.md`; evidencia privada `./.lab/web-port/acceptance/<run>/`.

**Interfaces:** consume catálogo, CoverageReport, FrameSummary, resultados E2E y evidencias manuales; produce matriz `escena/modo × navegador/OS × carga/fidelidad/gameplay/estabilidad/rendimiento`, estados PASS/PARTIAL/BLOCKED/NOT_RUN.

- [ ] Ejecutar únicamente suites nuevas: `python3 -m unittest discover -s ./tests/web_port -v`; `cd ./web && npm run typecheck && npm run test:unit && npm run build`. No correr suite histórica/preflight ni pruebas de integridad del Plan 2 como condición de cierre.
- [ ] Publicar el build recién generado; ejecutar `npm run test:e2e -- --project=chromium`, `--project=firefox` y `--project=webkit` contra el mismo build/contenido. Configurar esos nombres en Playwright. Registrar entorno/browser faltante, no simularlo.
- [ ] Probar en Safari y Chrome reales de MacBook por LAN: menús, todos los mapas en alcance, recorridos de cada modo, controles, audio, guardado, 30 ciclos y sesión de 60 min. Firefox y Windows/Linux se registran por equipo disponible; no declarar cobertura sin ensayo.
- [ ] Revisar vistas y diferencias frente a evidencia existente: fidelidad desconocida queda pendiente, no PASS. No lanzar el APK para resolverlo dentro de este plan sin cambio de alcance autorizado.
- [ ] Incorporar mediciones de tarea 12, recursos críticos faltantes, excepciones y peticiones fuera de origen. Cualquier defecto esencial impide PASS; priorizar corrección antes de más optimizaciones.
- [ ] Redactar cierre con contenido realmente funcional, bloqueos y alcance de cada plataforma. Enlazar manual, versiones fijadas y ubicación privada de evidencias sin secretos.
- [ ] Informar la decisión final de cada uno de los ocho objetos y distinguir pruebas originales de pruebas del port. Compilación C#, formatos válidos y capturas Android no sustituyen aceptación web, visual ni de todos los mapas.
- [ ] Parar servicios temporales propios y entregar instrucciones de arranque. Mantener commits/merge/push pendientes de autorización; no iniciar multiplayer ni siguiente iteración automáticamente.

**Aceptación G4:** acceso HTTP LAN y single player estables en la matriz efectivamente probada; G0–G4 y cobertura requerida completos para PASS global. Una demo de un mapa o tests sintéticos verdes no bastan.

## Comandos y resultados: reglas de interpretación

- Los comandos de este documento son para una sesión futura; **no se han ejecutado** al escribirlo.
- RED debe demostrar comportamiento ausente con el entorno de pruebas funcionando; no contar errores de descarga/configuración como TDD.
- Cada tarea termina con revisión propia de contratos, errores, cobertura y diff acotado. Si se autorizan commits, uno por unidad verde; no añadir datos privados ni mezclar trabajo previo del usuario.
- Confirmar rutas antes de trabajar: `step/rewrite` ya existe como worktree aislado; no recrearlo, limpiarlo ni borrar salidas ajenas.
- No hay una fecha de entrega ni esfuerzo total garantizado: el número de familias de componentes y recursos con recuperación parcial determina trabajo real.

## Autorrevisión documental

- [x] Separadas evidencia aceptada del Plan 2 y pruebas funcionales del nuevo cliente.
- [x] Incorporadas las rutas recuperadas, advertencias de fidelidad y tratamiento por dependencia de los ocho objetos, sin exigir compilación del proyecto Unity ni repetir Plan 2.
- [x] Stack aprobado, HTTP LAN sin contexto seguro y ausencia total de Unity reflejados en contratos y tareas.
- [x] Catálogo completo y expansión de cobertura impiden cerrar con una sola escena de muestra.
- [x] Incluidos menús, movimiento, combate, enemigos/objetivos, progreso, audio y recuperación.
- [x] Los cinco focos de revisión tienen pruebas asignadas.
- [x] Modelos de datos y firmas compartidos explícitos; los detalles dependientes del contenido se resuelven antes de sus consumidores.
- [x] Presupuestos de rendimiento etiquetados como propuestas; hardware pendiente no se convierte en resultado.
- [x] Safari real distinguido de WebKit headless; plataformas no probadas permanecen NOT_RUN.
- [x] Sin tareas ejecutadas, instalaciones del juego, servicios o commits en esta sesión.

## Fuentes para el ejecutor

- Documentación oficial citada en [investigación](../../analysis/tecnologias-port-web.md#9-fuentes-oficiales-consultadas); contrastar APIs con las versiones fijadas, no mezclar Babylon Lite/convencional.
- http-server, raíz explícita y flags de red/listado/cache: https://github.com/http-party/http-server#usage
- Vitest, CLI y patrones: https://vitest.dev/guide/cli.html
- Playwright, configuración/proyectos: https://playwright.dev/docs/test-configuration

**Handoff:** revisar este plan y su diseño antes de una sesión futura de ejecución. Esta sesión termina con documentación; no elegir ni iniciar implementación automáticamente.
