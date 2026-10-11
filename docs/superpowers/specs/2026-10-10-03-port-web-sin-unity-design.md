# Plan 3 — Diseño del port web sin Unity

**Fecha:** 2026-10-10. **Estado:** documentación del alcance y stack aprobados en conversación; especificación detallada para revisión junto al plan. **No autoriza ejecución en esta sesión.**

**Plan asociado:** [Plan 3 — implementación](../plans/2026-10-10-03-reimplementacion-web-single-player.md).
**Base técnica:** [investigación de tecnologías](../../analysis/tecnologias-port-web.md).

## 1. Objetivo y prioridad

Reimplementar Pixel Gun 3D 11.3.1 para navegadores de escritorio, completamente sin Unity. El servidor Linux headless entrega archivos por HTTP a una MacBook en la LAN; la MacBook ejecuta simulación, audio y renderizado.

Orden de prioridad:

1. Escenas y menús cargan, conservan su contenido y permiten navegar sin bloqueos.
2. Mapas conservados: geometría, disposición, materiales, iluminación y elementos de gameplay recuperables.
3. Single player funcional y estable, no únicamente un visor de mapas.
4. Fluidez, tiempos de carga y consumo de memoria controlados.
5. Servicios locales dummy que evitan dependencias online; multiplayer real fuera de alcance.

No se repiten pruebas de integridad del Plan 2. Su documentación es la línea base aceptada. No se recalculan hashes de originales, comparan APK/OBB, repiten preflights ni reejecuta el original como requisito de este plan.

## 2. Alcance y límites de cobertura

### Incluido

- Arranque web, menús necesarios para los recorridos locales, ajustes, selección de contenido, HUD, pausa, resultados y retorno al menú.
- Movimiento, cámara, colisiones, armas, daño, enemigos/objetivos cuando el modo original los requiera, muerte, reinicio y progresión local.
- Conversión y conservación de los mapas identificados en los datos; los mapas exclusivos de multiplayer pueden abrirse en un **modo de exploración local explícito**, sin afirmar que su modo online esté implementado.
- Inventario de cobertura de todas las escenas listadas en los datos existentes: los 109 archivos de nivel no se tratan como 109 mapas jugables.
- Menús exclusivamente online conservan su acceso/representación cuando corresponda, pero muestran disponibilidad deshabilitada; no simulan cuentas, compras o partidas reales.
- Guardado local y servicios dummy desacoplados del gameplay.
- Alojamiento estático HTTP LAN y pruebas de la nueva implementación.

El catálogo funcional distingue `bootstrap`, `menu`, `single-player`, `multiplayer-map`, `other`, y registra modos, rutas de navegación y componentes necesarios. Se construye a partir de las salidas existentes y de la lectura necesaria para convertir el contenido; **no es una nueva auditoría de integridad**.

No omitir mapas o rutas problemáticos para declarar el port completo. Una escena bloqueada lleva motivo y dependencias; si pertenece al alcance, impide PASS global. El primer mapa funcional es un hito intermedio, no el entregable final.

### Excluido

- Unity Editor, runtime Unity, Unity WebGL, emulación/streaming Android o renderizado remoto.
- Navegadores móviles, controles táctiles y publicación en tiendas.
- Multiplayer real, backend, cuentas reales, compras, anuncios, analítica y conexión a endpoints originales.
- Rediseño visual, remasterización, reemplazo de mapas por aproximaciones o incorporación de contenido nuevo.
- WebGPU obligatorio, PWA/service workers obligatorios, SharedArrayBuffer o WASM multihilo obligatorio.
- Instalar o ejecutar componentes del producto durante esta sesión de documentación.

## 3. Base existente y entradas

Evidencias aceptadas: [continuación Plan 2 del 2026-10-11](../../analysis/continuacion-plan-2-2026-10-11.md), [resultados históricos](../../analysis/conclusiones-y-bloqueos.md), [recursos](../../analysis/inventario-recursos.md), [dependencias](../../analysis/mapa-dependencias.md) y [arranque](../../analysis/flujo-arranque.md).

Actualización 2026-10-11: las salidas privadas están disponibles en `./.lab/runs/20261011T174958Z-completion/` de este checkout. Los cuatro proyectos C# recuperados compilan juntos sin errores; el inventario cubre 8.165 archivos/490.030 objetos, con campos de 490.022 recuperados y exports completos ejecutados. El plan identifica rutas a `managed/rebuild/`, staging, inventario refinado, medios y shaders. La salida original e IL se conservan para contrastar representaciones; los scripts sirven de referencia para TypeScript, no se ejecutan en el navegador.

Quedan ocho objetos con 332 bytes personalizados sin interpretar: siete referencias `FyberEditor` y una `LpOwerride`, sin definiciones en las DLL suministradas. El catálogo conserva cada registro y evalúa su dependencia respecto al runtime web. Excluir componentes de Editor/servicios fuera de alcance requiere evidencia; una función desconocida requerida bloquea las escenas afectadas hasta resolverse. No inventar campos ni excluir por nombre/tamaño, y no detener contenido independiente por una dependencia no demostrada.

AssetRipper conserva diagnósticos de layout en `BulletStackController`/`InputField`; los campos recuperados y referencias de shaders son la base para la conversión dirigida. Formato válido no certifica fidelidad. El proyecto Unity exportado no se compiló ni ejecutó y no es un prerrequisito del port sin Unity.

Las pruebas existentes ejecutaron el APK original: tutorial/menú dos veces desde instalación limpia, Farm con perfil derivado. No certifican todas las escenas ni el cliente nuevo. En otra máquina/checkout se reciben rutas explícitas a estas salidas; si faltan, se solicita ubicación/recuperación sin repetir silenciosamente Plan 2.

Los originales y salidas del Plan 2 permanecen de solo lectura. Las nuevas conversiones van a `./.lab/web-port/`; los datos derivados del juego y capturas no se publican automáticamente en Git.

## 4. Stack acordado

| Área | Tecnología |
|---|---|
| Lógica | TypeScript, módulos ES |
| Motor gráfico | Babylon.js convencional, WebGL 2 |
| Física | Havok WASM con integración oficial Babylon |
| Menús/HUD | HTML/CSS y recursos originales |
| Contenido | glTF 2.0/GLB + manifiestos JSON versionados |
| Construcción | Vite |
| Conversión | Python + herramientas externas de lectura/exportación ya disponibles; ninguna requiere Unity Editor |
| Pruebas nuevas | unittest para conversión; Vitest para contratos/lógica; Playwright para flujos de navegador |
| Distribución | Cliente estático, WASM y recursos bajo el mismo origen HTTP |

Las versiones exactas se fijan en la primera tarea de ejecución, contrastando requisitos oficiales y compatibilidad de paquetes. Babylon core/loaders comparten versión; Havok, Vite y herramientas se fijan por separado con lockfile. No usar `latest`, rangos flotantes o CDN en la distribución.

## 5. Arquitectura y límites

```text
Salidas existentes del Plan 2 (solo lectura)
            │ conversión selectiva, fuera del navegador
            ▼
  ./.lab/web-port/content/ — GLB, audio, atlas, manifiestos
            │ empaquetado de publicación
            ▼
  ./web/dist/ — raíz HTTP exclusiva
            │ LAN
            ▼
  Navegador de escritorio
    ApplicationState / UI
      ├─ SceneSession → Babylon + Havok
      ├─ LocalGame → movimiento, armas, enemigos, objetivos
      ├─ ContentRepository → recursos propios por escena
      └─ LocalServices → perfil, progreso, disponibilidad online
```

- **Conversión:** traduce formatos y campos originales a contratos web, conserva identidad por archivo + path_id y produce diagnósticos por contenido.
- **ContentRepository:** carga manifiestos y recursos locales; no conoce gameplay ni cuentas.
- **SceneSession:** es propietaria de escena, física, audio y suscripciones de una carga; dispone de liberación idempotente.
- **ApplicationState:** controla una sola sesión activa y las transiciones; un resultado asíncrono obsoleto no puede reactivar una escena cancelada.
- **LocalGame:** reglas del juego portadas según evidencia; no realiza peticiones online.
- **LocalServices:** implementa perfil/progreso local y estados explícitos de función online no disponible. No es una emulación del protocolo Photon.
- **UI:** presenta estado y envía acciones; no dirige directamente el render loop ni crea cuerpos físicos.

No recrear un runtime genérico de MonoBehaviour, C# o coroutines Unity. Mapear componentes necesarios a comportamientos concretos del nuevo juego. Separar datos y lógica para que el backend futuro no requiera rehacer los mapas.

## 6. Contrato de contenido y fidelidad

`SceneManifest` usa `schemaVersion: 1` y referencias relativas al origen HTTP. Contiene identidad, clasificación, paquetes visuales, nodos, colisiones, puntos de aparición, triggers, iluminación, audio y referencias de configuración de gameplay. `ContentCatalog` enumera todas las escenas y su estado de conversión/soporte. Un recurso crítico ausente produce error visible, no un éxito con contenido vacío.

Convención del runtime: coordenadas **dextrógiras, Y arriba, metros**; la conversión desde Unity se realiza una sola vez. GLB conserva la convención glTF. Datos complementarios deben usar la misma base; ajustar winding, normales, tangentes, rotaciones y escalas negativas de forma coherente. Conservar unidades originales y documentar cualquier factor observado; no inventar escalas.

GLB cubre representación gráfica, no todos los comportamientos de la escena original. JSON conserva información adicional: colliders, triggers, relaciones, navegación y eventos. No usar nombres amigables como identidad única.

Materiales: conservar atlas/UV, vertex colors, transparencia, alpha test, doble cara, skybox y lightmaps según los datos. No convertir automáticamente todo a PBR ni añadir luces que alteren la referencia. Skins y animaciones deben conservar huesos, poses y tiempos. Si falta una referencia perceptual, etiquetar la fidelidad como no verificada, no inventar una equivalencia.

Se carga el menú y después el mapa seleccionado, nunca todo el juego al inicio. Recursos compartidos tienen propiedad/recuento explícitos. Instancias y compresión solo después de tener una referencia funcional; no fusionar geometría si destruye triggers, identidad o colisiones.

Todos los WASM, fuentes y decodificadores se alojan localmente. La distribución no debe emitir peticiones a CDN, endpoints originales o telemetría.

## 7. Estados, errores e interacción

Estados: `boot`, `menu`, `loading`, `playing`, `paused`, `results`, `error`.

- Boot solo necesita capacidades y contenido local, no login/red externa.
- Menú → carga → juego es cancelable. Selecciones rápidas A/B solo activan B.
- Un error de mapa vuelve al menú mediante una acción explícita, sin recargar toda la página.
- Perder foco o pointer lock pausa y limpia teclas retenidas; recuperar foco no reanuda disparos ni juego automáticamente.
- Audio y captura de ratón se activan con gesto explícito. Rechazo del navegador produce instrucción visible; no crash.
- Context loss pausa y muestra recuperación; si no puede reconstruirse con seguridad, reiniciar la escena o volver al menú. No prometer recuperación transparente universal.
- Liberación idempotente de escena, física, audio, eventos, timers, UI y cargas pendientes.

Simulación fija a **60 Hz**, acumulador con máximo de **5 pasos por frame**; al pausar/restaurar se descarta tiempo pendiente para evitar ráfagas y saltos. Render independiente con interpolación cuando corresponda. Estos valores son decisiones del nuevo runtime, no afirmaciones sobre el original.

## 8. Single player y servicios locales

La primera sección vertical incluye un mapa original, movimiento/cámara, colisión, un arma, blanco/enemigo apropiado al modo, daño, muerte/reinicio, pausa y retorno al menú. Después se extiende por modos y componentes del catálogo.

Velocidades, FOV, daño, munición, cadencia, recarga, estados de enemigo, objetivos y condiciones de victoria se trasladan desde datos/código existente; registrar fuente de cada parámetro en el mapa de comportamientos. Valores provisionales solo en fixtures sintéticos, no como fidelidad aceptada del contenido real.

NPCs deben usar navegación adecuada al mapa y no cruzar paredes. Conservar datos de navegación utilizables; si no hay datos portables, generar navegación fuera del navegador desde la geometría y registrar esa derivación. La selección de una dependencia adicional de navegación debe justificarse antes de incorporarla; no bloquea tareas anteriores.

Guardado versionado local. Si está corrupto, es de una versión futura, el almacenamiento se deniega o se agota, iniciar sesión temporal con aviso y conservar la copia recuperable sin sobrescritura automática. No migrar cuentas ni compras reales. Servicios online devuelven `unavailable`, no éxitos fabricados.

El original bloquea Campaign después del tutorial hasta una primera partida multijugador. El cliente web permite tutorial → menú → Campaign mediante progreso local explícito, sin esperar ese servicio ni importar flags del perfil Android derivado. No informa una partida online completada; conserva objetivos y progresión del single player traducidos.

## 9. HTTP LAN y seguridad de distribución

Ruta objetivo: `http://<IP-LAN-del-servidor>:8080/` como puerto inicial configurable. Bind explícito a la IP LAN elegida, no publicar indiscriminadamente a Internet. Servir solo `./web/dist/`, sin listado de directorios ni acceso a originales, `.lab`, decompilados o archivos de entorno.

WebGL 2 y WASM/SIMD son capacidades requeridas; ausencia produce pantalla explicativa. HTTP LAN no es contexto seguro como localhost. No depender de WebGPU, service workers, HTTPS, memoria compartida ni flags especiales.

Build, WASM, audio y datos deben tener tipos MIME correctos. URLs relativas al despliegue y errores 404 reales: no devolver `index.html` cuando falte un binario o mapa. Versionar URLs de publicación para evitar mezclar manifiestos y recursos antiguos, sin volver a hashear originales.

No cambiar firewall, permisos administrativos, routing ni certificados automáticamente. Si el acceso LAN está bloqueado, registrar el bloqueo y pedir una decisión independiente.

## 10. Validación y umbrales

**Estas son pruebas del producto nuevo, no nuevas pruebas de integridad del original.**

### Funcionalidad y contenido

- Todas las escenas catalogadas tienen categoría, destino y estado explícitos.
- Todos los mapas en alcance cargan; rutas de menús locales no terminan en pantallas vacías o esperas online.
- Cada modo single player en alcance tiene recorrido de inicio, juego, muerte/reinicio o victoria y salida.
- Cero excepciones no controladas, rechazos no controlados o recursos críticos ausentes en recorridos aceptados.
- Cero peticiones fuera del origen del juego durante la sesión (no contar operaciones de instalación/build).
- Comparaciones visuales contra evidencia existente y escenas convertidas desde puntos de vista identificados; diferencias intencionadas documentadas, diferencias desconocidas no reciben PASS.

### Estabilidad

- **30 ciclos** de entrar/salir/reiniciar escenas representativas; no aumentar de forma acumulativa sesiones, cuerpos físicos, listeners o sonidos vivos tras liberar.
- **60 minutos** de single player con cambios de mapa y pausa; cero crashes, bloqueos irrecuperables o fallos de guardado que impidan continuar.
- Ensayos de 404, carga lenta/cancelada, WASM no disponible, almacenamiento denegado, pérdida de foco y contexto gráfico.
- Ausencia de APIs de medida de heap en un navegador no se interpreta como cero memoria; usar contadores de recursos y observación del proceso cuando sea posible.

### Rendimiento: presupuesto inicial propuesto

Meta: **60 fps**, resolución interna máxima inicial **1920×1080**, sin multiplicar automáticamente por todo el DPR Retina. Registrar tamaño de ventana y resolución real.

En un recorrido activo de **5 minutos**, después de **30 segundos** de calentamiento, sin pantallas de carga ni pestaña en segundo plano: mediana de intervalo entre frames ≤ **17,5 ms**, p95 ≤ **25 ms**, p99 ≤ **50 ms**. Registrar también pausas >100 ms y su causa. No presentar fps medios como único indicador.

En LAN de referencia, propuesta inicial: menú interactivo ≤ **5 s** desde navegación fría; mapa inicial jugable ≤ **10 s** desde selección fría y ≤ **5 s** con caché caliente. Son presupuestos del proyecto pendientes de confirmar contra tamaño de contenido y equipo; no garantías de la investigación. No ocultar un incumplimiento precargando todo ni quitando mapas.

Antes de evaluar estos presupuestos, registrar modelo/chip/RAM de MacBook, macOS, navegador/versión, energía y LAN. Si falta acceso al equipo, rendimiento real = NOT_RUN, nunca PASS por un ensayo headless. Ajustar un presupuesto exige documentar motivo y aprobación del usuario, no moverlo silenciosamente.

### Navegadores

Objetivo: Safari y Chrome actuales disponibles en la MacBook, más Firefox de escritorio; versiones exactas se anotan al ejecutar. Automatizar Chromium/Firefox/WebKit en Linux donde sea posible, pero WebKit Playwright no certifica Safari de marca. Comprobar distribución en Windows/Linux/macOS con hardware y versiones registrados antes de afirmar cobertura cruzada; las combinaciones sin equipo disponible quedan NOT_RUN.

## 11. Entregables y puertas

1. **G0:** entradas previas localizadas, catálogo/contratos y toolchain del nuevo cliente definidos; sin repetir Plan 2.
2. **G1:** primer mapa original visible y navegable desde menú por HTTP LAN; errores recuperables.
3. **G2:** sección vertical single player completa y calibrada; no confundirla con port completo.
4. **G3:** cobertura de escenas/menús/mapas/modos en alcance, sin omisiones silenciosas.
5. **G4:** aceptación funcional, visual, estabilidad y rendimiento en equipos reales; distribución y manual LAN.

Estados: PASS, PARTIAL, BLOCKED, NOT_RUN. PASS global requiere G0–G4 y la matriz completa; cualquier limitación de contenido, plataforma o referencia queda en el informe. La ausencia de evidencia no es aprobación.

## 12. Decisiones de esta documentación

El usuario aprobó el stack y pidió un plan explícito, sin implementación en esta sesión. Este diseño fija contratos y criterios propuestos para que el ejecutor no invente alcance durante el trabajo. Equipo de referencia y versiones reales se registrarán al ejecutar; el detalle de contenido se obtendrá del catálogo antes de ampliar el port. No hay commits, instalaciones del producto, conversiones, servidores ni pruebas del juego realizadas por este documento.
