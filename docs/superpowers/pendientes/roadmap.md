# Roadmap pendiente — Refinamiento y ampliaciones futuras

**Estado:** pendientes sin número de plan asignado. Hoja de ruta propuesta el 2026-10-11; no es autorización de implementación ni lista de requisitos para cerrar el Plan 3. Cada iteración tendrá su diseño y plan acotado cuando corresponda; no se inventan ahora APIs o estimaciones del contenido no estudiado.

**Punto de partida:** [Plan 3](../plans/2026-10-10-03-reimplementacion-web-single-player.md) entrega menú/tienda, Arena y multiplayer propio con tres mapas. [Diseño vigente](../specs/2026-10-10-03-port-web-sin-unity-design.md).

Estas ampliaciones se mantienen como pendientes. No reservan números para futuros planes; al seleccionar una para ejecución se redactará su plan concreto.

## Qué se aplaza y qué permanece en Plan 3

Esta hoja de ruta conserva el trabajo grande retirado del alcance inmediato: mapas restantes, familias adicionales de armas/enemigos, economía/progresión ampliada y campaña. Está desglosado por iteración o línea de trabajo, **no como planes de implementación detallados ya terminados**. Los detalles se redactan al seleccionar cada lote.

Menú, tienda simplificada, equipamiento persistente, Arena, deathmatch, duelo por equipos, captura de bandera y cooperativo permanecen en Plan 3. Sus partes 3A/3B/3C se ejecutan y completan dentro de esa misma primera iteración.

## Regla de expansión

Aceptar y jugar una entrega antes de ampliar. Cada incremento de contenido convierte **uno o dos mapas como máximo** y solo sus dependencias. Una nueva familia costosa de arma, enemigo, shader o modo se separa en una tarea/iteración propia, nunca se esconde en «convertir mapas restantes».

No comprometer convertir 70/74 mapas de golpe; el conteo jugable se determina por catálogo. Conservar procedencia y estado `deferred` permite retomar contenido sin rehacer recuperación. La campaña no es prioridad de las iteraciones próximas.

## Refinar el slice existente

**Objetivo:** que los mismos tres mapas y flujos soporten sesiones repetidas agradables y estables. **Sin campaña ni obligación de añadir mapas.**

- [ ] Recoger evidencia de partidas reales: fallos reproducibles, sensaciones de movimiento/disparo, legibilidad UI, equilibrio y dificultades de hosting.
- [ ] Priorizar defectos y mejoras acotadas en menú/tienda, controles, objetivos, netcode LAN, persistencia y rendimiento. Defectos esenciales que impiden el PASS de Plan 3 se arreglan allí, no se aplazan para llamarlo completo.
- [ ] Ajustar balance de las dos armas, dos monstruos y los modos con configuraciones trazables; no ampliar todo el catálogo económico.
- [ ] Mejorar reconexión/interpolación o experiencia del lobby solo cuando las partidas muestren la necesidad; cada cambio con ensayo de desconexión/latencia específico.
- [ ] Repetir aceptación de parejas afectadas y regresión del flujo completo; publicar informe con incidencias cerradas y pendientes priorizados.

**Salida:** versión refinada del mismo slice, sin regresiones esenciales y con evidencia de estabilidad. **Puerta hacia más contenido:** Plan 3 aceptado, defectos prioritarios del refinamiento resueltos y aprobación del siguiente lote.

## Incorporar mapas adicionales por lotes

**Objetivo:** demostrar que la conversión es repetible sin degradar lo ya jugable. Seleccionar **uno o dos mapas** para modos ya implementados, preferentemente sin familias de comportamiento nuevas.

- [ ] Evaluar candidatos del catálogo por dependencias, relevancia para jugadores y esfuerzo observado; fijar IDs y modos antes de convertir.
- [ ] Crear una tarea independiente por mapa: conversión → fidelidad/colliders/spawns → partida completa → carga/recursos/rendimiento.
- [ ] Publicar solo mapas aceptados del lote y repetir regresión de mapas existentes. Un mapa bloqueado conserva estado/motivo; cambiar el lote exige decisión documentada.
- [ ] Medir coste real de incorporación y actualizar el procedimiento para el próximo lote, sin prometer cubrir todo el archivo original.

**Salida:** incremento de uno o dos mapas aceptados, no «todos los restantes». Lotes posteriores repiten este patrón con alcance nuevo.

## Iteraciones posteriores — Líneas independientes, no un megaplan

| Línea | Candidatos | Condición y límite |
|---|---|---|
| Más mapas Arena/multiplayer | Nuevos escenarios del catálogo | Lotes de 1–2, usando modos estables; validación individual. |
| Armas/enemigos/equipamiento | Familias ausentes y mayor variedad de tienda | Un conjunto pequeño explícito por iteración; balance y efectos de red probados. |
| Modos adicionales | Los no seleccionados, Sandbox u otros recuperados | Elegir un modo, documentar reglas y cerrar su ciclo en un mapa antes de expandir. |
| Multiplayer ampliado | Más jugadores/salas, espectador, reingreso en ronda | Necesidad demostrada y prueba de carga; cuatro plazas/una sala no se convierten silenciosamente en escala ilimitada. |
| Hosting remoto | Servidor accesible por Internet, HTTPS/WSS, operación y protección | Plan propio para red, persistencia, acceso y recuperación; contenedor LAN no certifica servicio público. |
| Progresión/servicios | Cuentas, economía más amplia, estadísticas, cosméticos | Decisión de producto separada; no reconectar automáticamente servicios originales ni simular compras reales. |

El orden entre estas líneas se decide por feedback. No son dependencias obligatorias unas de otras ni autorización para implementarlas en paralelo.

## Campaña — Backlog de largo plazo

Se conserva como posibilidad futura, **fuera del Plan 3 y de la siguiente iteración, sin fecha comprometida**. Solo reconsiderar tras varias iteraciones refinadas y una decisión explícita del usuario.

Antes de planificarla:

- [ ] Definir experiencia deseada, capítulos/niveles, progresión, narrativa, desbloqueos y relación con perfil/tienda.
- [ ] Leer fuentes/evidencia relevantes. El tutorial/menú y Farm con perfil derivado son referencias parciales: no prueban campaña completa, final de nivel ni progresión natural.
- [ ] Resolver comportamiento de onboarding y desbloqueos sin requerir servidores originales; hacerlo aquí, no imponerlo a Arena/multiplayer actuales.
- [ ] Elegir **un nivel o segmento jugable** como primer slice de campaña y fijar aceptación propia. Farm puede ser candidato por evidencia disponible, no elección automática.
- [ ] Extender por segmentos aceptados, nunca añadir de golpe todos los capítulos al Plan 3.

## Trazabilidad del alcance retirado

| Obligación del Plan 3 anterior | Nuevo destino |
|---|---|
| Antigua tarea 10: convertir todos los mapas y familias | Pendiente de ampliación de mapas, con IDs y límite 1–2 por lote. |
| Tutorial → menú → Campaign y progreso de campaña | Iniciativa de campaña a largo plazo. No bloquea menú/Arena. |
| Mapas multiplayer solo en exploración | Tres mapas del slice tienen reglas jugables según matriz; los demás se aplazan. |
| Completar todas las armas/enemigos/menús comerciales | Iteraciones independientes de contenido/progresión. |
| Multiplayer sustituido por dummy | Sustituido en Plan 3B/3C por sala y servidor real propios. |
| Aceptación global del catálogo completo | Cada release acepta su selección explícita; preserva el resto como deferred. |

Esta hoja de ruta evita que el trabajo aplazado vuelva a entrar como requisito implícito de la primera entrega.
