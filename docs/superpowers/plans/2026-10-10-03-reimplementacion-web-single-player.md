# Plan 3 — Primera iteración: vertical slice web, Arena y multiplayer local

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement the linked subplans task-by-task. Steps use checkbox (`- [ ]`) syntax. Ejecución directa; este documento no autoriza implementación, delegación, commits ni despliegue en esta sesión.

**Goal:** Entregar menú → tienda/equipamiento → Arena o partida multijugador local → resultados → menú, con un mapa Arena y dos mapas multijugador.

**Architecture:** Conversión selectiva de recursos del Plan 2; cliente Babylon/Havok; servidor propio autoritativo para sala, partidas y economía local. Alojamiento en computadora del usuario o contenedor Linux, accesible por LAN.

**Tech Stack:** Cliente aprobado: TypeScript, Babylon.js convencional, WebGL 2, Havok WASM, HTML/CSS, Vite, GLB/JSON. Servidor propuesto: Node.js/TypeScript/WebSocket; unittest, Vitest y Playwright para verificación.

**Spec:** [Diseño vigente](../specs/2026-10-10-03-port-web-sin-unity-design.md). **Estado:** planificación reformulada el 2026-10-11; ninguna tarea del producto ejecutada. Se conserva este nombre de archivo histórico para mantener enlaces.

## Qué cambia respecto al plan anterior

- El entregable final es un **vertical slice aceptado**, no el port de todo el catálogo.
- Se elimina la antigua tarea 10 de ampliar cobertura a todos los mapas/modos. No se traslada esa obligación a otra tarea de cierre.
- Solo tres mapas: A1 Arena, M1/M2 multiplayer. Los IDs reales se seleccionan de las salidas existentes; no son nombres inventados de mapas.
- Campaign, tutorial original y Sandbox se aplazan. Campaign tampoco entra en la siguiente iteración.
- Multiplayer es real y propio: crear/unirse a sala, jugar con otras personas y terminar partidas. Servir archivos o explorar un mapa no basta.
- Tienda funcional con moneda local y catálogo pequeño; sin pagos ni emulación de servicios originales.
- Modos confirmados para esta primera iteración: deathmatch, duelo por equipos, captura de bandera y cooperativo contra monstruos, además de Arena.

## Global Constraints

Aplican a cada subplan todas las restricciones y presupuestos del diseño. No repetir Plan 2; originales de solo lectura; cero Unity/CDN/endpoints originales; escritorio HTTP LAN; sin cambios automáticos de firewall. Solo se convierten dependencias del contenido seleccionado. No iniciar implementación en esta sesión documental.

Catálogo completo **no** significa conversión completa: una entrada `deferred` con motivo es conservación documental, no bloqueo del slice. Una dependencia desconocida de un mapa **seleccionado** sí impide aceptarlo. No se puede retirar silenciosamente un seleccionado para obtener PASS.

## Review Focus

1. Carga cancelada/foco/contexto gráfico sin recursos o input retenidos — 3A.3–3A.4 y 3C.5.
2. Colliders, transformaciones y navegación coherentes entre cliente y servidor — 3A.2, 3A.5 y 3B.1.
3. Compras concurrentes, perfil corrupto y reinicio sin pérdida silenciosa — 3B.2.
4. Mensajes duplicados/inválidos, cliente desincronizado y desconexión del creador/portador — 3B.3–3B.5 y 3C.3.
5. Contenedor/LAN realmente accesibles desde otro equipo, WASM local y contenido sin escapes — 3A.3, 3B.6, 3C.5–3C.6.

## Entregas pequeñas y orden de ejecución

**3A + 3B + 3C = un único Plan 3 y una única primera iteración completa.** Son divisiones internas para ejecutar el trabajo en partes manejables. Los modos de 3C no se aplazan al roadmap pendiente.

| Subplan | Tareas | Resultado verificable |
|---|---|---|
| [3A — Arena jugable](./2026-10-11-03a-arena-jugable.md) | 3A.1–3A.6 | Menú → A1 → combate/oleadas → muerte/resultado → reinicio/menú. Primer hito jugable. |
| [3B — Tienda y multiplayer base](./2026-10-11-03b-tienda-multiplayer-local.md) | 3B.1–3B.6 | Compra/equipo persistente y deathmatch M1 entre dos computadoras por LAN. |
| [3C — Modos y entrega](./2026-10-11-03c-modos-y-entrega.md) | 3C.1–3C.6 | M2 y tres modos adicionales, capacidad cuatro clientes, contenedor, aceptación final. |

Cada tarea tiene archivos, contrato, prueba y una salida propia. Ejecutar secuencialmente y revisar cada entrega antes de ampliar; no esperar a 3C para probar partidas reales. Si una tarea descubre otra familia de comportamiento, dividirla en unidades verificables de ese mismo contenido, no absorber el catálogo completo.

3A y 3B son hitos utilizables, pero no se llaman Plan 3 completo. El cierre de Plan 3 exige los tres subplanes; las [ampliaciones del roadmap pendiente](../pendientes/roadmap.md) no lo bloquean.

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
- En tarea 3A.1, registrar los ocho por `SourceRef`, clase, ensamblado, bytes opacos, referencias a escenas y decisión sustentada. No excluir por nombre, tamaño o la suposición de que pertenecen a publicidad.
- Una dependencia demostrada de Editor o de un servicio excluido puede quedar fuera del runtime web, conservando su registro y evidencia. `LpOwerride` empieza sin clasificar; no atribuirle una función sin evidencia.
- Si un objeto afecta una función o dato requerido por una escena en alcance, esa escena queda bloqueada hasta recuperar su definición o reconstruir el campo/comportamiento con evidencia. Procesar contenido independiente mientras tanto; no eliminar el mapa ni inventar valores.

## Contratos mínimos compartidos

Rutas futuras, no archivos creados en esta sesión. 3A crea `./shared/` y 3B lo amplía sin duplicar modelos cliente/servidor.

- `./shared/src/content.ts`: `SourceRef = { file: string; pathId: string }`; `SceneEntry = { id: string; source: SourceRef; scope: 'slice' | 'deferred' | 'non-playable'; reason: string; modeIds: ModeId[]; status: 'pending' | 'converted' | 'functional' | 'accepted' | 'blocked' }`.
- `SliceSelection = { schemaVersion: 1; arenaSceneId: string; multiplayerSceneIds: [string, string]; supportedPairs: { sceneId: string; modeId: ModeId }[]; weaponIds: [string, string]; enemyIds: [string, string] }`. IDs distintos y presentes en catálogo; matriz obligatoria del diseño. Config de reglas y economía se congela con evidencia en 3A.1/3B.2 antes de consumidores.
- `ContentRelease = { schemaVersion: 1; releaseId: string; selection: SliceSelection; scenes: SceneEntry[] }`; publicación contiene solo seleccionados y dependencias. Manifiestos: GLB, nodos/TRS, colliders, spawns, triggers, luz/audio y gameplay; referencias locales sin traversal/esquemas externos, basis `RH_Y_UP_METERS`.
- `./shared/src/game.ts`: `ModeId = 'arena' | 'deathmatch' | 'team-deathmatch' | 'capture-the-flag' | 'coop'`; `Vec3 = { x: number; y: number; z: number }`; `PlayerInput = { sequence: number; moveX: number; moveZ: number; yaw: number; pitch: number; jump: boolean; fire: boolean; reload: boolean }`.
- `./shared/src/simulation.ts`: `Simulation.step(inputs: ReadonlyMap<string, PlayerInput>, dt: number): WorldSnapshot`; `snapshot(): WorldSnapshot`; `dispose(): void`. `WorldSnapshot` contiene tick, poses/vida/arma de jugadores, entidades del modo, marcador/fase y última secuencia aplicada por jugador. Arena y servidor consumen las mismas reglas con adaptadores distintos de física/tiempo/persistencia.
- `./shared/src/profile.ts` (3B): `GuestProfile = { schemaVersion: 1; id: string; coins: number; ownedWeaponIds: string[]; equippedWeaponId: string; revision: number }`; `PurchaseRequest = { requestId: string; weaponId: string }`; `PurchaseResult = { ok: true; profile: GuestProfile } | { ok: false; reason: 'insufficient-funds' | 'already-owned' | 'unknown-item' | 'storage-failed' }`. Identidad autenticada por token de invitado, precio siempre servidor.
- `./shared/src/protocol.ts` (3B): handshake `Hello = { protocolVersion: 1; releaseId: string; guestToken: string }`; comandos discriminados `create/join/ready/start/input/leave`; respuestas `welcome/lobby/snapshot/results/error`. Datos concretos se fijan y validan en 3B.3; desconocidos, no finitos, versiones/releases distintos se rechazan. Token no va en URL ni logs.

No construir un runtime genérico Unity/MonoBehaviour. Separar contenidos, reglas y transporte; UI envía acciones y no crea física ni decide autoridad. Tests de conformidad Python/TS para contenido; schemas compartidos para cliente/servidor.

## Comandos futuros y reglas de trabajo

3A.1 define workspace raíz `./package.json`, lockfile y versiones fijadas. Scripts previstos desde raíz: `npm run typecheck`, `npm run test:unit`, `npm run build`, `npm run test:e2e -- <filtro>`, `npm run test:server`, `npm run start:lan -- --host <IP> --port 8080`; cada script se añade en la tarea que lo necesita. Conversor: `python3 -m unittest discover -s ./tests/web_port -v`.

Los comandos aún no existen ni se han ejecutado. RED significa comportamiento ausente con el runner funcionando, no error de instalación. Cada tarea: prueba específica fallando, implementación mínima, prueba verde y revisión de diff. No repetir suites históricas ni agregar pruebas que solo dupliquen texto documental. Commits/merge/push requieren autorización aparte.

## Cierre y fuera de alcance

Informe futuro `./docs/analysis/resultado-plan-3.md`: matriz seleccionada mapa/modo × navegador × carga/fidelidad/gameplay/red/estabilidad; evidencia real, fallos y NOT_RUN. PASS requiere 3A–3C, persistencia, multiplayer externo por LAN, contenedor y presupuestos del diseño. Ningún test sintético o captura del APK sustituye estas pruebas.

Aplazados: resto de mapas y catálogo, modos complejos adicionales, campaña, cuentas/pagos/red global. Registrar y enlazar futura iteración; no estimar esfuerzo por el número de archivos recuperados.

**Handoff:** revisión del diseño y subplanes antes de ejecutar; método directo conservado. Esta sesión entrega documentación, no inicia el producto ni crea commits.
