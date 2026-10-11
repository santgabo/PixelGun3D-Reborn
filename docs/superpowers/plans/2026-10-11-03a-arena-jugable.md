# Plan 3A — Primera entrega jugable de Arena

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Ejecutar por tarea con checkboxes; no autoriza implementación/commits en la sesión documental.

**Goal:** Menú → Arena A1 → combatir oleadas → resultado/reinicio → menú.
**Architecture:** Conversión dirigida, cliente Babylon/Havok, reglas compartidas preparadas para servidor y perfil local temporal.
**Tech Stack:** Python/unittest; TypeScript/Babylon/WebGL 2/Havok/Vite/Vitest/Playwright.
**Spec:** [Diseño](../specs/2026-10-10-03-port-web-sin-unity-design.md), [contratos y entradas comunes](./2026-10-10-03-reimplementacion-web-single-player.md).

## Global Constraints

Exactamente A1, M1, M2 en la selección; solo A1 se convierte aquí. Dos armas y dos arquetipos propuestos. Sin Campaign/tutorial original ni auditoría global. RH/Y arriba/metros; 60 Hz y máximo 5 pasos. Salidas privadas en `./.lab/web-port/`. Aplican todas las restricciones del diseño.

## Review Focus

IDs/nombres duplicados (3A.1); ejes/espejo/colliders (3A.2); carga cancelada/404 (3A.3); foco/disparo/muerte duplicados (3A.4); enemigos sin ruta y recursos retenidos (3A.5–3A.6).

## Tarea 3A.1 — Congelar selección y contratos del slice

**Files:** crear `./tools/web_port/{__init__,contracts,catalog}.py`, `./tests/web_port/test_catalog.py`, `./shared/src/{content,game,simulation}.ts`, `./shared/tests/content.test.ts`, `./shared/package.json`, configuración raíz `./package.json`, `./package-lock.json`, `./.node-version`, `./tsconfig.json`; crear `./docs/web/{content-scope,behavior-map,toolchain}.md`; actualizar `.gitignore`.
**Interfaces:** consume entradas Plan 2; `build_catalog(evidence: dict) -> dict`, `validate_selection(catalog: dict, selection: dict) -> None`; produce `SliceSelection`, contenido y contratos de simulación definidos en Plan 3. Configuración de armas/enemigos/oleadas lleva ID, valores y fuente/adaptación declarada.

- [ ] Localizar recuperación existente y leer selectivamente catálogo/código para elegir A1, M1 y M2 con la matriz requerida. Fijar dos armas compatibles con una familia y dos monstruos; señalar conflictos antes de convertir. Registrar los ocho opacos y seguir solo referencias necesarias. No inferir IDs por nombres.
- [ ] Escribir `test_selection_has_one_arena_two_distinct_mp_maps`, `test_required_pairs_are_supported`, `test_deferred_scene_is_not_required`, `test_selected_blocker_prevents_acceptance`, `test_large_path_id_roundtrips`; ejecutarlos con unittest y Vitest: RED por contrato ausente.
- [ ] Implementar catálogo, manifiesto de selección y schemas Python/TS. Conservar entradas aplazadas por identidad/motivo, sin investigar todos sus comportamientos. Fijar toolchain tras consultar documentación oficial; workspace raíz `shared`/`web` y scripts `typecheck`, `test:unit`, `build`, `test:e2e`; carpeta servidor se incorpora en 3B. Excluir derivados, builds, resultados y datos privados de Git.
- [ ] Repetir tests: GREEN. Documentar IDs reales, compatibilidad, valores/fuentes y funciones excluidas. La selección aún no certifica conversión o juego.

**Aceptación:** selección finita y trazable; ninguna dependencia exige convertir el resto del catálogo. Si no hay combinación viable de tres mapas, detener esta selección con conflicto concreto, no inflar el alcance.

## Tarea 3A.2 — Convertir A1 y sus dependencias

**Files:** crear `./tools/web_port/{unity_reader,references,transforms,glb_writer,materials,animation,ui_assets,audio}.py`, `./tools/export_web_scene.py`, `./tests/web_port/test_arena_conversion.py`.
**Interfaces:** `convert_scene(data_root: Path, recovery_root: Path, scene_id: str, output: Path) -> dict`; CLI `python3 ./tools/export_web_scene.py --data-root "$DATA" --recovery-root "$RUN" --scene "$A1_ID" --output "$OUT"`. Output nuevo, fuera de entradas; produce manifiesto y medios locales referenciados.

- [ ] Fixtures propios: padre/hijo con escala negativa, winding/normal/UV, collider desplazado, huesos/clip, sprite de atlas y audio loop. Tests comparan coordenadas/poses/tiempos esperados y bloquean campos críticos ausentes.
- [ ] Ejecutar `python3 -m unittest discover -s ./tests/web_port -p 'test_arena_conversion.py' -v`: RED. Implementar solo familias usadas por A1, armas/enemigos/UI seleccionados; reutilizar exports trazables. Si animación/material exige trabajo independiente, separar por familia con fixture propio dentro de A1, sin añadir mapas.
- [ ] Repetir: GREEN. Convertir A1; contrastar layouts advertidos y shaders necesarios con campos recuperados. No aceptar automáticamente YAML/GLB como fidelidad comprobada.
- [ ] Emitir informe privado de dependencias y faltantes; resumir en `content-scope.md`. Una función desconocida requerida bloquea A1; los ocho objetos no requieren resolución universal.

**Aceptación:** paquete A1 con geometría, colisiones, medios y procedencia; integración y percepción se comprueban en runtime.

## Tarea 3A.3 — Menú, carga y publicación mínima por LAN

**Files:** crear `./web/{package.json,index.html,vite.config.ts,playwright.config.ts}`, `./web/src/{main,content/repository,app/controller,app/capabilities,runtime/scene-session,runtime/resource-scope,ui/menu,ui/settings}.ts`, `./web/scripts/{publish-content,serve-lan}.mjs`, tests colocados junto a módulos y `./web/tests/e2e/scene-loading.spec.ts`.
**Interfaces:** `loadScene(id: string, signal: AbortSignal): Promise<SceneManifest>`; `SceneSession.dispose(): void` idempotente; `publish:content -- --source <dir> --release <id>` publica por allowlist; `serve:lan -- --host <IP> --port 8080` sirve exclusivamente build. `AppState` incluye boot/menu/loading/playing/paused/results/error; lobby se añade en 3B.

- [ ] Tests de capacidades ausentes, manifiesto incompatible, path traversal/symlink, WASM 404, A lento cancelado por B y dispose doble. E2E exige menú visible y cero requests externos. Ejecutar pruebas dirigidas: RED.
- [ ] Implementar shell/UI original necesaria, carga de A1, WASM/decoders locales, propiedad de recursos y retorno al menú tras error. Publicador no copia `.lab`, DLL, originales o secretos; release incompleto no reemplaza activo. HTTP sin listado/dotfiles/fallback HTML de binarios, MIME correctos.
- [ ] Ejecutar `npm run typecheck`, `npm run build`, publicación explícita y `npm run test:e2e -- scene-loading`: GREEN. Tests usan build recién publicado; no ejecutar Vite build sobre distribución activa.
- [ ] Inspeccionar A1 en navegador desde vistas identificadas y documentar diferencias; acceso localhost y LAN se registran por separado. Añadir botones de futura tienda/multiplayer identificados como pendientes hasta 3B, sin falsas partidas.

**Aceptación:** menú → A1 visible → menú con carga cancelable y errores recuperables. No se presenta como Arena jugable todavía.

## Tarea 3A.4 — Movimiento, armas y vida

**Files:** crear `./shared/src/{player,weapons,damage}.ts`, `./web/src/{runtime/clock,input/keyboard-mouse,input/pointer-lock,gameplay/physics-adapter,ui/hud}.ts`, tests y `./web/tests/e2e/combat.spec.ts`.
**Interfaces:** `PlayerInput`/`WorldSnapshot` comunes; `PhysicsAdapter.move(bodyId: string, input: PlayerInput, dt: number): Vec3`; `raycast(from: Vec3, to: Vec3): Hit | null`; `Hit = { entityId: string; point: Vec3; distance: number }`. `WeaponSystem.step(input: PlayerInput, dt: number): ShotEvent[]`; eventos tipados alimentan reglas compartidas. Elegir familia concreta según 3A.1, sin simular como hitscan un arma que no lo es.

- [ ] Tests: pared/pendiente/escalón, límite cadencia/munición/recarga, pared bloquea impacto, muerto no dispara, muerte única, foco perdido limpia input, reloj descarta backlog al pausar. Runner funcional → RED.
- [ ] Implementar controlador Havok y reglas para las dos armas seleccionadas; calibrar con configuración/fuentes. Activar audio/pointer lock por gesto; rechazo muestra instrucción. No acoplar velocidad a fps ni meter transporte en reglas.
- [ ] `npm run test:unit -- combat` y `npm run test:e2e -- combat`: GREEN; comprobar movimiento, disparo, muerte y reinicio en A1 real. Configurar nombres de tests para estos filtros.
- [ ] Registrar diferencias frente a fuentes y liberar cuerpos/audio/input al reiniciar; revisión visual del HUD/armas. Preservar API del adaptador para prueba headless 3B.1.

**Aceptación:** combate y reinicio reales en A1, aunque oleadas todavía pendientes.

## Tarea 3A.5 — Oleadas, navegación y Arena

**Files:** crear `./shared/src/{enemies,waves,modes/arena}.ts`, `./tools/web_port/navigation.py`, `./tests/web_port/test_navigation.py`, `./web/src/gameplay/local-game.ts`, `./web/tests/e2e/arena.spec.ts`; tests unitarios junto a reglas.
**Interfaces:** `findPath(from: Vec3, to: Vec3): readonly Vec3[] | null`; `ArenaRules.step(dt: number, events: readonly GameEvent[]): ModeState`; `GameEvent` discrimina daño/muerte/oleada; `ModeState` define fase, oleada, puntuación y resultado. Ampliar contrato común antes del consumidor; simulación no depende del DOM.

- [ ] Tests: enemigo no atraviesa pared, sin ruta no se teletransporta, solo se inicia siguiente oleada tras completar la actual, bajas/puntos una vez, muerte/final y reinicio vacían entidades. Ejecutar unittest de navegación y unitarias Arena: RED.
- [ ] Reutilizar datos navegables recuperados o derivar grafo offline de colisiones con procedencia documentada. Implementar los dos arquetipos y reglas/oleadas configuradas. Si Arena original es interminable, derrota/salida cierran sesión; no inventar campaña o victoria narrativa.
- [ ] Repetir: GREEN. E2E `npm run test:e2e -- arena`: menú → jugar → oleadas/daño → muerte → resultado → reiniciar → salir. Resultado no se basa solo en un botón de debug.
- [ ] Contrastar UI/audio/animaciones de enemigos y corregir defectos del recorrido; lo no demostrado queda pendiente de fidelidad.

**Aceptación:** primer recorrido completo jugable sin tutorial/Campaign ni servidor original.

## Tarea 3A.6 — Guardado local y cierre de la primera entrega

**Files:** crear `./web/src/services/local-profile.ts`, `./web/tests/e2e/arena-lifecycle.spec.ts`, `./docs/web/acceptance-3a.md`.
**Interfaces:** `LocalProfileStore.load(): { settings: Settings; arenaBest: number; temporary: boolean }`; `save(value): { persisted: boolean; warning?: string }`. Arma inicial/equipo local provisional; no saldo comercial ni compra persistente antes de 3B.

- [ ] Tests de JSON corrupto/futuro, denegación/cuota, pausa/reanudación y diez ciclos de entrar/salir/reiniciar. La copia recuperable no se sobrescribe y contadores exclusivos vuelven a base.
- [ ] Implementar ajustes/récord local, avisos y recuperación. Pasar tests y E2E `npm run test:e2e -- arena-lifecycle` contra A1 publicado.
- [ ] Jugar A1 manualmente en navegador real, registrar versión/equipo, verificar menú/controles/audio/resultado y medir presupuesto inicial. Pruebas sin equipo se marcan NOT_RUN.
- [ ] Documentar qué está jugable, evidencias y bloqueos; pasar a 3B tras esta revisión. No exigir M1/M2 aquí ni llamar completo al Plan 3.

**Aceptación 3A:** entrega Arena utilizable; tienda, multiplayer y cierre final siguen explícitamente pendientes.
