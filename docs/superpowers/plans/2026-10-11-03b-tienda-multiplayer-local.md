# Plan 3B — Tienda y primera partida multijugador local

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Ejecución directa por tarea; no autoriza ejecutar ni crear commits en la sesión documental.

**Goal:** Comprar/equipar, crear o unirse a sala y completar deathmatch M1 desde dos computadoras por LAN.
**Architecture:** Un servidor dedicado propio sirve cliente/API/WebSocket; reglas autoritativas compartidas y perfiles invitados persistentes.
**Tech Stack:** Cliente de 3A; Node.js/TypeScript/WebSocket propuestos, Vitest y Playwright. Versiones/paquetes se fijan tras consulta oficial en 3B.1.
**Spec:** [Diseño](../specs/2026-10-10-03-port-web-sin-unity-design.md), [contratos comunes](./2026-10-10-03-reimplementacion-web-single-player.md). Depende de 3A.

## Global Constraints

Una sala activa, cuatro jugadores máximo, sin Photon/servicios originales; mismo origen para HTTP/API/WebSocket. Simulación 60 Hz, snapshots 20 Hz. Solo M1 se convierte aquí. Dos armas seleccionadas; moneda local y token de invitado. Aplican restricciones y presupuestos del diseño.

## Review Focus

Física headless divergente (3B.1); compra concurrente/almacenamiento fallido (3B.2); release/protocolo/sala incompatibles (3B.3); inputs inválidos y resultados duplicados (3B.4); creador desconectado/foco suspendido (3B.5); localhost confundido con acceso remoto (3B.6).

## Tarea 3B.1 — Servidor mínimo y prueba de simulación headless

**Files:** crear `./server/{package.json,tsconfig.json}`, `./server/src/{main,config,http,simulation/physics-adapter,simulation/session}.ts`, `./server/tests/headless-physics.test.ts`; ampliar workspace/scripts raíz; `./docs/web/server-runtime.md`.
**Interfaces:** `startServer({ host, port, contentRoot, dataRoot }): Promise<{ close(): Promise<void> }>`; HTTP estáticos y `GET /health`; adaptador implementa contrato físico 3A.4 y consume `Simulation` compartida. Script raíz `start:lan -- --host <IP> --port 8080` reemplaza hosting solo estático; conserva CLI, agrega API/WS.

- [ ] Test headless con fixtures: movimiento frente a pared/escalón, disparo obstruido y misma entrada/resultado de reglas en adaptadores cliente/servidor dentro de tolerancia documentada. Test cierre libera timers/cuerpos; iniciar sin display/GPU. RED antes de implementación.
- [ ] Fijar runtime/biblioteca WebSocket y verificar adaptador Havok en Node contra docs oficiales y ensayo real; registrar versiones y resultado. Si no funciona, resolver adaptador alternativo y paridad antes de seguir. No ocultar este riesgo hasta el final.
- [ ] Implementar servidor HTTP con las restricciones del publicador 3A.3 y simulación compartida; añadir `test:server`. `npm run test:server -- headless-physics`, `npm run typecheck` y `npm run build`: GREEN.
- [ ] Confirmar que Node no necesita DOM/GPU para funcionar; registrar coste de tick y cierre. No instalar Unity ni cambiar el renderer cliente para resolver el servidor.

**Aceptación:** proceso headless viable y contrato de colisión probado; todavía no afirma multiplayer.

## Tarea 3B.2 — Perfil invitado y tienda persistente

**Files:** crear `./shared/src/profile.ts`, `./server/src/{profiles/store,profiles/service,shop/catalog,shop/service,routes/profile,routes/shop}.ts`, `./web/src/{services/server-profile,ui/shop,ui/loadout}.ts`, `./server/tests/shop.test.ts`, `./web/tests/e2e/shop.spec.ts`.
**Interfaces:** `createGuest(): Promise<{ token: string; profile: GuestProfile }>`; `purchase(token: string, request: PurchaseRequest): Promise<PurchaseResult>`; `equip(token: string, weaponId: string): Promise<GuestProfile>` rechaza no poseídas. Rutas `POST /api/guests`, `GET /api/profile`, `POST /api/shop/purchase`, `POST /api/loadout`; token de invitado en autorización, sin logs sensibles. Contratos del Plan 3; volumen dataRoot persistente.

- [ ] Fijar `economy.json` privado/versionado con release: saldo inicial suficiente para probar segunda arma, precio positivo, recompensa local y fuentes/adaptaciones. Tests: precio enviado por cliente ignorado, saldo insuficiente, ítem desconocido, mismo requestId devuelve mismo resultado, dos compras concurrentes solo cobran una, equipar no poseída falla, error de disco no confirma éxito. RED.
- [ ] Implementar escritura atómica serializada de perfil + deduplicación en una unidad persistida; token opaco autenticado, sin cuenta externa. Equipar se aplica siguiente ronda. Perfil corrupto/futuro se conserva y muestra recuperación explícita. Añadir límites de cuerpo/validación y rechazar solicitudes cross-origin inesperadas.
- [ ] `npm run test:server -- shop` y `npm run test:e2e -- shop`: GREEN; reiniciar servidor con mismo dataRoot y navegador con mismo token conserva saldo/equipo, también tras repetir requestId. Fallo de almacenamiento del navegador produce sesión temporal avisada.
- [ ] Conectar menú/tienda/equipamiento a Arena y futuras partidas; Arena usa equipo obtenido y récord local, no concede moneda al servidor. Mostrar moneda de laboratorio y catálogo reducido con recursos seleccionados, sin botones de compra real.

**Aceptación:** compra/equipamiento efectivos y persistentes; ni mock de éxito ni toda la economía original.

## Tarea 3B.3 — Protocolo, sala y preparación de partida

**Files:** crear `./shared/src/protocol.ts`, `./server/src/{network/validation,network/connection,rooms/room}.ts`, `./web/src/{network/client,ui/lobby}.ts`, `./server/tests/room.test.ts`, `./web/tests/e2e/lobby.spec.ts`.
**Interfaces:** handshake/comandos comunes; `Room.create(ownerId, config)`, `join(playerId)`, `ready(playerId, value)`, `start(playerId)`, `leave(playerId)`. Config contiene modeId/sceneId autorizados, releaseId y reglas de límites. Primer soporte: deathmatch/M1. Fijar schemas discriminados antes de consumidores; validar permisos en servidor, no solo UI.

- [ ] Tests de protocolo/release distintos, token inválido, quinto cliente, segunda conexión del mismo perfil, modo/mapa no soportado, start sin permiso/readiness, late join y creador desconectado. Segunda conexión simultánea del mismo perfil se rechaza; entrada en ronda espera próxima. RED.
- [ ] Implementar una sala, listado/creación/unión, ready y barrera de carga: iniciar simulación cuando todos los participantes activos confirman paquete correcto; timeout expulsa al fallido y vuelve a lobby para nuevo inicio. Desconexión del creador transfiere control al conectado más antiguo.
- [ ] Definir validación de tamaño/frecuencia, secuencias, números finitos y origin WebSocket permitido. Inputs de otra identidad o comandos malformados se rechazan sin tumbar servidor; token no se pasa en URL.
- [ ] `npm run test:server -- room` y `npm run test:e2e -- lobby`: GREEN con clientes independientes. Cierre de sala vacía libera timers/estado; desconexión limpia slot.

**Aceptación:** lobby real de cuatro plazas, sin afirmar todavía combate sincronizado.

## Tarea 3B.4 — Deathmatch autoritativo

**Files:** crear `./shared/src/modes/deathmatch.ts`, `./server/src/{matches/match,matches/loop,matches/rewards}.ts`, `./server/tests/deathmatch.test.ts`; extender protocolo con snapshots/resultados tipados.
**Interfaces:** `Match.step(inputs, dt): WorldSnapshot`; servidor fija loadout desde perfil al comenzar, aplica reglas comunes 3A, snapshots por tick y confirmación de secuencias. `finish(matchId): MatchResult` idempotente; recompensa persistida una vez por matchId/jugador. `MatchResult` contiene ganador/empate, puntuaciones y motivo de cierre.

- [ ] Tests: input repetido/futuro/no finito, velocidad/cadencia imposibles, disparo por pared, daño/muerte/baja únicos, respawn válido, tiempo/puntos/empate, cliente no concede moneda ni cambia equipo durante ronda. RED.
- [ ] Fijar límites/respawn/desempate desde fuentes y adaptación explícita; implementar tick 60 Hz con máximo 5 pasos, snapshots 20 Hz y autoridad de movimiento/combate. No aceptar posición o hit result como verdad del cliente.
- [ ] `npm run test:server -- deathmatch`: GREEN con cuatro clientes sintéticos. Confirmar resultados comunes, recompensa idempotente bajo reintento y muerte simultánea, retorno al lobby.
- [ ] Medir tick/backlog; corregir divergencias antes de sumar otro modo. Sin lag compensation avanzada en esta iteración LAN.

**Aceptación:** ronda deathmatch completa en servidor, comprobada por clientes de prueba; falta integración visual en M1.

## Tarea 3B.5 — Cliente de partida y conversión de M1

**Files:** actualizar conversor para dependencias de M1; crear `./web/src/{network/replication,network/reconciliation,gameplay/network-game,ui/scoreboard}.ts`, `./web/tests/e2e/multiplayer.spec.ts`; tests unitarios colocados junto a replicación.
**Interfaces:** `NetworkGame.apply(snapshot: WorldSnapshot): void`, `send(input: PlayerInput): void`, `leave(): Promise<void>`; interpolación de otros jugadores y reconciliación local con ack de input. Escena y release según selección congelada.

- [ ] Convertir **solo M1** y dependencias faltantes con fixtures dirigidos; verificar spawns/colliders y mapa real, sin abrir lote global de mapas.
- [ ] Tests de snapshots repetidos/antiguos, input retenido al perder foco, cierre durante carga, desconexión durante partida y contexto gráfico perdido. Servidor sigue jugando si un cliente muestra overlay. RED.
- [ ] Implementar presentación de jugadores, disparos/vida/marcador/resultados; separar efectos visuales de autoridad. Tras pérdida de red mostrar error/reintento al lobby, sin duplicar jugador ni afirmar reingreso a ronda en curso.
- [ ] `npm run test:e2e -- multiplayer`: GREEN con dos contextos reales de navegador; ambos ven movimiento, daño, muerte, respawn y mismos resultados. Verificar equipo comprado y salida limpia.

**Aceptación:** deathmatch M1 integrado y jugable; automatización local aún no demuestra LAN entre equipos.

## Tarea 3B.6 — Prueba real LAN y cierre del flujo de usuario

**Files:** crear `./docs/web/{run-lan,acceptance-3b}.md`, `./web/tests/e2e/user-journey.spec.ts`; evidencias en `./.lab/web-port/acceptance/3b/`.
**Interfaces:** comandos raíz `npm run build`, `npm run publish:content -- --source "$CONTENT_DIR" --release "$RELEASE_ID"`, `npm run start:lan -- --host "$LAN_IP" --port 8080`; servidor usa solo build/publicación/dataRoot explícitos.

- [ ] E2E perfil nuevo → tienda → compra/equipo → crear/unirse → deathmatch M1 → resultado/recompensa → lobby/menú → reinicio/perfil. Añadir rechazo de WASM ausente y release mezclado.
- [ ] Ejecutar suites dirigidas, build y publicación; verificar HTTP/API/WebSocket y cero servicios externos con distribución real, no solo dev server.
- [ ] Alojar en computadora del usuario o Linux; dos computadoras distintas abren URL LAN y completan ronda. Registrar hosts/navegadores, resultados coherentes y desconexión del creador sin caída del servidor. Si falta segundo equipo, NOT_RUN y cierre parcial.
- [ ] Entregar instrucciones de arranque/parada y resolver fallos del recorrido antes de 3C. Cuatro participantes y contenedor se cierran en 3C; no exigir más mapas aquí.

**Aceptación 3B:** tienda y partida real entre equipos. Ya se puede jugar y recoger feedback sin esperar los modos adicionales.
