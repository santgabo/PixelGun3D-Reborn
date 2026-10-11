# Plan 3C — Modos seleccionados, segundo mapa multijugador y entrega

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Ejecutar directamente por tarea; esta documentación no autoriza implementación ni commits.

**Goal:** Completar la matriz de tres mapas/cinco modos y entregar servidor nativo o contenedor con aceptación LAN.
**Architecture:** Extender las reglas/sala de 3B, reutilizar combate, tienda e IA, convertir únicamente M2 y empaquetar una instalación autocontenida.
**Tech Stack:** Stack de 3A/3B; Docker Compose para despliegue propuesto, sin orquestador adicional.
**Spec:** [Diseño](../specs/2026-10-10-03-port-web-sin-unity-design.md), [Plan 3](./2026-10-10-03-reimplementacion-web-single-player.md). Depende de 3B. Esta parte es obligatoria dentro de la primera iteración del Plan 3: duelo por equipos, captura de bandera y cooperativo fueron confirmados por el usuario; no se aplazan a futuras iteraciones.

## Global Constraints

Solo M2 adicional; no cuarto mapa. Matriz: A1/Arena, M1/deathmatch+equipos, M2/deathmatch+bandera+cooperativo. Mismos dos tipos de arma y dos de monstruo; cuatro plazas, una sala. Ninguna tarea admite «resto del catálogo». Presupuestos, fuentes y privacidad del diseño aplican completos.

## Review Focus

Mapa aparentemente convertido sin colisiones/spawns válidos (3C.1); puntuación doble/fuego amigo (3C.2); bandera huérfana tras desconexión (3C.3); IA divergente/último jugador muerto (3C.4); persistencia/puerto/memoria y LAN reales (3C.5–3C.6).

## Tarea 3C.1 — Convertir M2 y validar su contrato multimodo

**Files:** ampliar `./tools/web_port/` solo para dependencias faltantes de M2; crear `./tests/web_port/test_multimode_map.py`, `./web/tests/e2e/map-m2.spec.ts`; actualizar `./docs/web/content-scope.md`.
**Interfaces:** mismo CLI/SceneManifest de 3A; M2 añade spawns por equipo, bases/banderas y navegación/zonas de aparición de monstruos. `validateModeMap(manifest, modeId): ValidationResult` comparte reglas estructurales cliente/servidor; `ValidationResult` contiene ok y errores con ID/fuente.

- [ ] Fixtures/tests de dos bases distintas, spawns fuera de sólidos, rutas accesibles, enemy spawn inválido y ausencia de dependencia crítica. RED; implementar validación y conversión dirigida.
- [ ] Convertir M2, contrastar cada marcador/componente con fuente/adaptación registrada en selección. No añadir por aproximación un mapa nuevo ni cambiar M1 para evitar un bloqueo.
- [ ] Repetir unittest y `npm run test:e2e -- map-m2`: GREEN; cargar M2 y jugar deathmatch con la implementación existente. Revisar vistas, audio, colisiones y liberación.
- [ ] Publicar release que contiene A1/M1/M2 y actualizar aceptación de M2 como mapa; CTF/cooperativo solo se marcan funcionales tras sus tareas.

**Aceptación:** segundo mapa multijugador real; sin incorporar otros mapas o familias no requeridas.

## Tarea 3C.2 — Duelo por equipos en M1

**Files:** crear `./shared/src/modes/team-deathmatch.ts`, `./server/tests/team-deathmatch.test.ts`, `./web/tests/e2e/team-deathmatch.spec.ts`; ampliar lobby/marcador existentes.
**Interfaces:** `TeamDeathmatchRules` implementa el contrato común de reglas y produce estado con teamId por jugador, teamScores y MatchResult. Sin segundo motor de combate ni protocolo de daño paralelo.

- [ ] Fijar asignación, spawn, fuego amigo, límite y desempate desde fuentes/adaptaciones. Tests 2v2, suicidio, baja única, desconexión de un equipo y final por tiempo/puntos. RED.
- [ ] Implementar reglas/colores/marcador y selección en sala; impedir inicio sin al menos un jugador por equipo. Elegir spawns válidos de M1, sin aceptar equipo enviado por input cliente.
- [ ] `npm run test:server -- team-deathmatch`, `npm run test:e2e -- team-deathmatch`: GREEN; mismos equipos/marcador/resultado en clientes, partida terminable con dos y con cuatro participantes.
- [ ] Registrar diferencias explícitas y verificar retorno a lobby para cambiar de modo sin reiniciar proceso.

**Aceptación:** duelo completo en M1; mapas adicionales no son condición.

## Tarea 3C.3 — Captura de bandera en M2

**Files:** crear `./shared/src/modes/capture-the-flag.ts`, `./server/tests/capture-the-flag.test.ts`, `./web/tests/e2e/capture-the-flag.spec.ts`; ampliar representación/HUD de objetivos.
**Interfaces:** `FlagState = { teamId: string; state: 'at-base' | 'carried' | 'dropped'; carrierId: string | null; position: Vec3; returnAtTick: number | null }`; transición autoritativa dentro de reglas compartidas. Valores/regla de captura y devolución fijados antes de consumidores.

- [ ] Tests: recoger rival, impedir doble portador, muerte/salida del portador, devolución manual/tiempo, captura con bandera propia según regla fijada, empate y dos eventos en mismo tick. RED.
- [ ] Implementar máquina de estados de bandera, bases/triggers M2, marcador y objetivo visible; el servidor valida cercanía/estado y resuelve orden de eventos. Desconectado no retiene bandera; un cliente no declara capturas.
- [ ] `npm run test:server -- capture-the-flag`, `npm run test:e2e -- capture-the-flag`: GREEN; dos clientes completan captura/resultado, cuatro clientes verifican disputa y consistencia.
- [ ] Probar nuevo round y cambio de modo sin banderas/entidades residuales. Registrar reglas adaptadas y vistas.

**Aceptación:** ciclo de bandera completo y recuperación de portador ausente; no ampliar a todos los mapas CTF originales.

## Tarea 3C.4 — Cooperativo contra monstruos en M2

**Files:** crear `./shared/src/modes/coop.ts`, `./server/tests/coop.test.ts`, `./web/tests/e2e/coop.spec.ts`; reutilizar navegación/enemigos/oleadas de 3A y replicación de 3B.
**Interfaces:** `CoopRules` usa WorldSnapshot con entidades enemy, oleada, participantes vivos/muertos y resultado. IA/daño/oleadas solo avanzan en servidor; cliente representa snapshots, sin ejecutar una segunda IA autoritativa.

- [ ] Fijar dificultad/oleadas y respawn entre oleadas con fuentes/adaptaciones. Tests de daño concurrente al mismo enemigo, una muerte/recompensa, ausencia de ruta, último jugador muerto, abandono y reinicio. RED.
- [ ] Implementar modo con los dos monstruos seleccionados, navegación M2 y mismo inventario; política explícita de derrota grupal, fin y retorno al lobby. Sin revivir complejo, companions ni nuevas familias de enemigos.
- [ ] `npm run test:server -- coop`, `npm run test:e2e -- coop`: GREEN con dos y cuatro clientes. Todos observan mismos monstruos/oleada/resultado; enemigos no atraviesan geometría.
- [ ] Probar rotación Arena → multiplayer → cooperativo → menú; Arena local y servidor no comparten estado accidentalmente. Medir tick con máxima oleada configurada.

**Aceptación:** cooperativo jugable completo en M2 reutilizando sistemas existentes, sin campaña.

## Tarea 3C.5 — Contenedor, recuperación y diagnóstico

**Files:** crear `./deploy/{Dockerfile,compose.yaml,.env.example}`, `./.dockerignore`, `./docs/web/{run-container,troubleshooting,performance}.md`, `./server/tests/deployment.test.ts`, `./web/src/diagnostics/{frame-metrics,resource-counts}.ts`, `./web/tests/e2e/{deployment,lifecycle}.spec.ts`.
**Interfaces:** `docker compose -f ./deploy/compose.yaml up --build -d`; host LAN y puerto desde variables documentadas, contenedor escucha internamente en todas sus interfaces pero solo publica IP/puerto elegidos. Volumen de perfiles writable separado de contenido read-only. `/health` informa listo solo si release y servicios inicializaron.

- [ ] Tests de 404/MIME, allowlist, traversal/symlink, release incompleto, datos persistentes tras reinicio, error de escritura, caída de servidor y volver al lobby. Tests de percentiles sobre secuencias conocidas y limpieza tras 30 ciclos; RED.
- [ ] Empaquetar servidor/build con versiones fijadas, proceso sin privilegios y cierre ordenado; contenido privado mediante montaje read-only de release previamente publicado. No enviar `.lab`, APK/OBB, DLL, tokens o fuentes recuperadas al contexto Docker. No descargar recursos durante la partida ni publicar imagen con datos privados automáticamente.
- [ ] Implementar métricas locales sin telemetría, contadores de escenas/cuerpos/listeners/audio y tick/RTT. `npm run test:server -- deployment` y E2E deployment/lifecycle: GREEN. Context loss, foco y carga cancelada no acumulan recursos/red.
- [ ] `docker compose -f ./deploy/compose.yaml config` valida configuración; arrancar, completar partida desde otro equipo, comprar y reiniciar conservando perfil. Parar con `docker compose -f ./deploy/compose.yaml down` sin borrar volumen. Documentar arranque nativo, contenedor, logs, actualización/reversión de release y limpieza explícita.

**Aceptación:** contenedor Linux desplegable y usado por LAN, con datos persistentes. Docker ausente o prueba externa no realizada = NOT_RUN; un Dockerfile solo no demuestra hosting.

## Tarea 3C.6 — Aceptación final limitada a la matriz seleccionada

**Files:** crear `./docs/web/acceptance.md`, `./docs/analysis/resultado-plan-3.md`, `./web/tests/e2e/slice-coverage.spec.ts`; evidencia privada `./.lab/web-port/acceptance/3c/`.
**Interfaces:** `buildCoverageReport(selection: SliceSelection, results: ScenarioResult[]): CoverageReport` en `./shared/src/coverage.ts`; ScenarioResult por mapa/modo/plataforma con estado/evidencia; falta de pareja seleccionada impide PASS, entrada deferred no lo impide. Tests en `./shared/tests/coverage.test.ts`.

- [ ] Test de cobertura: exigir las seis parejas del diseño (A1 una, M1 dos, M2 tres), impedir omitir bloqueadas, distinguir NOT_RUN de PASS y no exigir catálogo aplazado. Implementar reporte y pasar tests.
- [ ] Ejecutar suites nuevas de conversión, `npm run typecheck`, `npm run test:unit`, `npm run test:server`, build/publicación y E2E por proyectos chromium/firefox/webkit configurados. No repetir Plan 2. Registrar versiones y runners faltantes.
- [ ] Safari/Chrome reales en MacBook, otro equipo LAN, cuatro clientes de capacidad, 30 ciclos y 60 minutos de sesión; completar compra/equipo/Arena y todos los modos de la matriz. Medir presupuestos del diseño por escenario representativo con equipo/resolución/red registrados, incluido cooperativo máximo configurado.
- [ ] Revisar vistas/fidelidad y errores; desconocido no recibe PASS. Documentar ocho objetos por relevancia al slice: los ajenos pueden permanecer pendientes. Capturas APK y C# compilado no sustituyen evidencia web.
- [ ] Resolver defectos esenciales y emitir PASS/PARTIAL/BLOCKED/NOT_RUN por recorrido. No bajar umbrales ni quitar mapas para cerrar. Detener servicios temporales propios y enlazar manuales y hoja de ruta; no iniciar siguiente iteración automáticamente.

**Aceptación Plan 3:** flujo completo, tres mapas y modos seleccionados funcionales, hosting nativo/contenedor, LAN/persistencia/estabilidad demostradas. El resto del juego queda documentado para futuro y no es condición de cierre.
