# Plan 3 — Diseño del vertical slice web, Arena y multijugador local

**Revisión:** 2026-10-11. Sustituye el alcance anterior de port completo/single player. Petición del usuario: reformular la documentación, sin implementar el juego en esta sesión.

**Plan:** [Plan 3 y sus entregas](../plans/2026-10-10-03-reimplementacion-web-single-player.md). **Después:** [roadmap pendiente](../pendientes/roadmap.md). Se conserva el nombre histórico del archivo del Plan 3 para no romper enlaces.

## 1. Resultado esperado y alcance

Al terminar el Plan 3 debe existir una primera iteración jugable: abrir el navegador, recorrer el menú, comprar y equipar en una tienda local, jugar Arena o crear/unirse a una partida multijugador real, ver resultados y volver al menú. El usuario puede alojar el servidor en su computadora o desplegarlo como contenedor; otras computadoras acceden por LAN. No depende de los servidores originales.

Convertir primero todo el catálogo retrasa la primera partida; entregar solo single player con botones online deshabilitados no cumple el flujo solicitado. Se eligen entregas pequeñas que terminan en recorridos jugables y acumulan capacidad.

| Decisión | Alcance de esta revisión |
|---|---|
| Mapas | **Tres mapas jugables originales:** uno de Arena (`A1`) y dos multijugador (`M1`, `M2`). Menús no cuentan como mapas. |
| Primer hito | Arena en A1; después deathmatch en M1. M2 se incorpora en una tarea propia. |
| Single player | Solo Arena. Campaign, tutorial original y Sandbox no son prerrequisitos. Sí hay instrucciones de controles en UI. |
| Multijugador | Deathmatch, duelo por equipos, captura de bandera y cooperativo contra monstruos, confirmados para esta primera iteración. |
| Tienda | Compra, saldo, propiedad y equipamiento con moneda local; catálogo reducido, sin pagos. |
| Hosting | Un servidor dedicado por instalación, una sala activa, máximo inicial de **4 jugadores**, acceso por URL y listado local de esa sala. |
| Campaña | Futuro lejano: fuera del Plan 3 **y de la siguiente iteración**. |

**Alcance confirmado:** los cuatro modos multijugador y Arena forman parte de la primera iteración y se completan dentro del Plan 3. 3A, 3B y 3C son divisiones internas de su ejecución, no versiones futuras. Menú, tienda y equipamiento persistente también pertenecen al cierre del Plan 3. La economía inicial simplificada fue confirmada por el usuario; capacidad y sala única siguen siendo propuestas de diseño, no características verificadas del original.

Tres mapas adopta la formulación «un mapa [Arena] y dos mapas multijugador». No se aumenta a cuatro por disponibilidad de recursos. Cerrar con solo dos requiere revisar explícitamente selección y aceptación; un fallo de conversión no reduce por sí solo el alcance.

## 2. Selección y cobertura

`A1`, `M1`, `M2` son roles de selección, **no IDs recuperados**. La primera tarea los vincula a `SourceRef` reales del Plan 2. No elegir Farm por ser el único mapa adicional probado: esa evidencia corresponde a Campaign y no demuestra aptitud para estos modos.

| Rol | Recorridos obligatorios |
|---|---|
| A1 | Arena individual: oleadas, enemigos, puntuación, muerte/final, resultado/reinicio. |
| M1 | Deathmatch y duelo por equipos. |
| M2 | Deathmatch, captura de bandera y cooperativo contra monstruos. |

No se exige cada modo en cada mapa. Seleccionar M2 tras comprobar bases, spawns y navegación adecuados en las fuentes. Si ningún candidato soporta esa combinación sin rediseñar el mapa, registrar el conflicto antes de congelar selección; no inventar soporte, añadir un cuarto mapa ni eliminar un modo silenciosamente.

El catálogo de conservación registra las entradas existentes como seleccionadas, aplazadas o no jugables. No exige convertirlas todas. Las aplazadas conservan identidad/motivo para futuro, no bloquean el PASS del slice y no aparecen como disponibles para jugar. Los 109 archivos de escena documentados no equivalen a 109 mapas; 70/74 no se adopta como conteo verificado.

Límites propuestos: **dos armas** de una misma familia recuperada —una inicial y otra comprable—, **dos arquetipos de monstruo** compartidos entre Arena/cooperativo, un perfil visual de jugador y dos colores de equipo. Si las fuentes requieren más familias para los recorridos elegidos, explicitar el coste antes de congelar alcance. Precios, saldo inicial, recompensas y límites de partida se fijan en configuración local trazable; no se replica toda la economía original.

## 3. Base técnica conservada

- TypeScript, Babylon.js convencional, WebGL 2, Havok WASM, HTML/CSS, Vite, GLB y JSON versionado. La [investigación previa](../../analysis/tecnologias-port-web.md) fundamenta el cliente; su exclusión histórica del multiplayer queda sustituida.
- Sin Unity Editor/runtime/WebGL, emulación Android, streaming o renderizado remoto. Escritorio; móviles fuera.
- Consumir salidas aceptadas del [Plan 2](../../analysis/continuacion-plan-2-2026-10-11.md), sin repetir hashes, staging, decompilación global ni inventario. Tabla de entradas en Plan 3.
- Originales/recuperación de solo lectura; derivados y evidencias privadas nuevas en `./.lab/web-port/`. No publicar automáticamente assets recuperados en Git.
- Registrar los ocho objetos opacos. Investigar dependencias de A1/M1/M2 y UI seleccionada; lo desconocido requerido bloquea ese contenido. Lo ajeno al slice puede seguir pendiente. No excluir por nombre/tamaño ni exigir resolver todo el catálogo.
- Coordenadas RH/Y arriba/metros; `pathId` decimal como string. Conservar geometría, jerarquías, colliders, materiales, atlas, iluminación, audio y animaciones requeridos; no reconstruir mapas aproximados ni reinterpretar todo como PBR.
- Cero CDN, telemetría y endpoints originales durante juego. Recursos y conexiones pertenecen al despliegue propio.
- WebGL 2 y WASM/SIMD requeridos. HTTP LAN no presupone contexto seguro; sin dependencia de WebGPU, service workers, SharedArrayBuffer o flags especiales.
- Sin cambios automáticos de firewall, certificados o routing. Exposición pública a Internet fuera del plan.

Las 1.982 fuentes C# compiladas son referencia, no runtime del producto. Tutorial/menú y Farm del APK no certifican estos mapas ni la red nueva. Localizar las salidas privadas al ejecutar: su disponibilidad no se presupone en cada worktree.

## 4. Servidor y autoridad

```text
Plan 2 (solo lectura) → conversión selectiva → paquete A1/M1/M2
                                                 │
Navegadores ← HTTP / WebSocket → Servidor propio sin pantalla/GPU
  Babylon + Havok                  archivos web y API
  UI / audio / presentación        sala y simulación autoritativa
  Arena local                      perfiles / tienda / volumen
```

Propuesta nueva: **Node.js + TypeScript y WebSocket**, un proceso que aloja estáticos, API de perfil/tienda y sala autoritativa, también empaquetable en contenedor Linux. El host juega desde navegador como un cliente más. No portar Photon. Versiones y biblioteca WebSocket se contrastan con documentación oficial y se fijan en 3B.

Servidor determina movimiento válido, impactos, daño, munición, puntuación, equipos, banderas, monstruos y fin. Clientes envían intenciones; no se aceptan saldos, kills o posiciones finales declaradas por el cliente. Compartir reglas puras y datos de colisión/navegación. La física autoritativa requiere prueba temprana headless: **compatibilidad de Havok en Node no demostrada**. Si falla, decidir adaptador alternativo con pruebas de paridad antes de continuar; no trasladar autoridad al cliente como parche.

Propuesta: simulación **60 Hz**, máximo **5 pasos** de recuperación por ciclo, snapshots **20 Hz**, interpolación remota y reconciliación local por secuencia de input. Sin rollback/compensación avanzada de latencia; objetivo LAN. Medir con cuatro clientes antes de añadir modos. Sin cluster, matchmaking global, NAT traversal, relay ni migración del host.

Sala: `lobby → loading → playing → results → lobby`. Creador configura/inicia; si abandona, el conectado más antiguo recibe ese control. El proceso dedicado continúa si se cierra el navegador del creador. Si cae el servidor, termina la partida y el cliente ofrece reintentar/volver; no se promete recuperar la ronda tras reiniciar contenedor.

Entrada durante `playing`: esperar en lobby a la próxima ronda. Desconexión: retirar jugador, liberar slot y resolver objetivos de modo. Puede volver al lobby con su perfil; reingreso a ronda en curso y espectador quedan para futuro.

## 5. Menú, tienda y persistencia

Flujos obligatorios:

1. Perfil nuevo → menú → tienda → comprar segunda arma → equipar → Arena → resultado/reinicio → menú.
2. Menú → multijugador → crear/unirse → mapa/modo → ready/inicio → partida compartida → resultados → lobby → menú.
3. Reiniciar navegador/servidor → recuperar saldo/inventario/equipo → volver a jugar.

Perfil de invitado por instalación. Servidor emite token opaco y guarda perfil, saldo, inventario y equipo en volumen local con escrituras atómicas serializadas. Navegador conserva token y ajustes; no importar cuentas Android ni usar ID público como credencial. Almacenamiento del navegador denegado: sesión temporal con aviso, sin promesa de persistencia entre visitas.

Servidor valida precio, saldo, propiedad, deduplica `requestId` y aplica compra como transacción. Solicitudes concurrentes no duplican gasto ni generan saldo negativo. Equipo queda fijado al comenzar ronda; cambios posteriores se aplican en la siguiente. Moneda de laboratorio identificada como tal. Solo resultados multijugador autoritativos conceden moneda persistente; Arena guarda récords locales y no genera recompensas confiables para servidor.

3A usa adaptador de perfil local para Arena; 3B incorpora tienda/servidor persistentes. El adaptador inicial no cuenta como tienda terminada. Perfil corrupto/futuro no se sobreescribe; fallo de escritura no devuelve éxito. Ajustes locales fallidos se recuperan en memoria con aviso.

## 6. Ciclo mínimo completo por modo

Contrastar reglas/parámetros con C# y datos al preparar cada modo; registrar adaptaciones. Completo se refiere a su ciclo jugable, no a toda la plataforma comercial.

| Modo | Criterios |
|---|---|
| Arena | Oleadas configuradas, spawns, IA/navegación, ataques, puntuación, muerte/final, reinicio y salida; sin Campaign. |
| Deathmatch | Spawn/respawn, bajas individuales, límite tiempo/puntos, desempate explícito y resultados comunes. |
| Duelo por equipos | Dos equipos, spawns, política de fuego amigo, puntos por equipo, fin/resultados. |
| Captura de bandera | Dos bases, recoger/transportar/soltar/devolver/capturar, regla de bandera propia, muerte/desconexión del portador, marcador/cierre. |
| Cooperativo | Monstruos/oleadas autoritativos, daño compartido, bajas únicas, respawn entre oleadas, derrota del grupo/resultados. |

Perder foco pausa Arena y descarta tiempo acumulado. En multiplayer solo libera input y muestra overlay: el servidor continúa. Recuperar contexto gráfico no duplica entidades/eventos. Salir libera escena, física, audio, listeners y suscripción de partida.

## 7. Aceptación proporcionada al slice

- **3A:** A1 jugable de menú a resultado/reinicio con contenido real. Primera entrega utilizable.
- **3B:** tienda persistente y deathmatch M1 con dos navegadores en computadoras distintas por LAN. Pestañas locales no sustituyen esa prueba.
- **3C:** matriz A1/M1/M2, modos seleccionados, cuatro clientes de prueba y arranque nativo/contenedor. Al menos dos participantes en computadoras distintas; cuatro clientes automatizados prueban capacidad, no cuatro equipos físicos.
- Cero excepciones no controladas, recursos críticos ausentes o llamadas externas. Inyectar protocolo/release incompatible, sala llena, mensajes inválidos, desconexión, compra duplicada y fallo de persistencia.
- **30 ciclos** de cargar/salir/reiniciar/reconectar al lobby sin acumulación de recursos; **60 minutos** con cambios de modo/mapa. Equipo o participantes ausentes: NOT_RUN.
- Presupuesto cliente propuesto conservado: máximo interno inicial 1920×1080; 5 min activos tras 30 s de calentamiento; mediana ≤17,5 ms, p95 ≤25 ms, p99 ≤50 ms; registrar pausas >100 ms. Menú frío ≤5 s, mapa frío ≤10 s/caliente ≤5 s. No relajar sin decisión documentada.
- Servidor/cuatro clientes: coste de tick p95 ≤16,7 ms propuesto; registrar RTT, jitter, bytes/s y edad de snapshots, sin backlog creciente ni divergencia permanente. No extrapolar LAN a Internet.
- Safari/Chrome reales en MacBook por LAN: objetivo principal. Playwright Chromium/Firefox/WebKit cubre regresión; WebKit no certifica Safari de marca. Windows/Linux/Firefox reales: registrar disponibilidad, sin afirmar cobertura no probada.

PASS significa **slice aceptado**, nunca catálogo completo. Requiere mapas/modos obligatorios y pruebas LAN/contenedor. PARTIAL/BLOCKED/NOT_RUN identifican defectos/evidencia ausente; contenido aplazado por diseño no hace PARTIAL el slice.

## 8. Expansión posterior

Resto de mapas, armas, enemigos, cosméticos, modos adicionales, matchmaking público, cuentas globales, pagos, clanes, rankings y eventos pasan a la hoja de ruta. Ninguna tarea del Plan 3 obliga a «completar todo lo restante».

Siguiente iteración: refinar estos tres mapas y flujos. Después, contenido por lotes de uno o dos mapas. Campaign es una iniciativa independiente sin fecha ni dependencia para estos cierres; requiere nueva decisión tras varias iteraciones refinadas.

Esta documentación no instala dependencias, convierte contenido ni levanta servidores. Las propuestas técnicas de capacidad y hosting quedan visibles para revisión previa a ejecución; los modos y el flujo de tienda/equipamiento pertenecen al alcance confirmado.
