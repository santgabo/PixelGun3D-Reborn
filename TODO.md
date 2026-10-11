# Continuación autorizada del Plan 2 — 2026-10-11

[Informe vigente y evidencias](./docs/analysis/continuacion-plan-2-2026-10-11.md).

- [x] Instalar y comprobar la suite local de recuperación y runtime.
- [x] Recuperar y autenticar APK/OBB originales sin modificarlos.
- [x] Decompilar los cuatro ensamblados y compilar juntos los scripts recuperados.
- [x] Inventariar todos los archivos Unity y exportar proyecto/recursos; conservar ocho objetos con campos opacos y tipos ausentes como bytes originales.
- [x] Recuperar Android completo en Smali y documentar Java/instrucciones alternativas.
- [x] Completar y documentar gameplay/tutorial/menú del original, repetir desde AVD limpio y cerrar procesos; comprobar Farm offline con perfil derivado separado.

# Plan 3 reformulado — primera iteración jugable

[Diseño](./docs/superpowers/specs/2026-10-10-03-port-web-sin-unity-design.md) · [Plan 3](./docs/superpowers/plans/2026-10-10-03-reimplementacion-web-single-player.md) · [Roadmap pendiente](./docs/superpowers/pendientes/roadmap.md) · [Convención de rutas](./docs/README.md).

Revisión 2026-10-11 solicitada por el usuario: reducir/dividir el plan y documentar futuro. Solo planificación; no autoriza implementación, instalaciones del producto, commits o servidores en esta sesión.

## Documentación completada

- [x] Conservar stack aprobado: TypeScript, Babylon.js convencional, WebGL 2, Havok WASM; sin Unity y solo navegadores de escritorio.
- [x] Sustituir el port de todo el catálogo por un slice de tres mapas: uno Arena y dos multijugador.
- [x] Eliminar la antigua tarea 10 de expansión universal; separar tareas y cierres verificables por entrega.
- [x] Incluir menú, tienda con moneda local, equipamiento y multiplayer propio real con hosting nativo/contenedor.
- [x] Documentar propuesta de servidor autoritativo, una sala/cuatro jugadores y pruebas de red/persistencia.
- [x] Separar la siguiente iteración de refinamiento y los futuros lotes de uno o dos mapas.
- [x] Sacar Campaign/tutorial original/Sandbox del slice; campaña tampoco entra en la siguiente iteración.
- [x] Preservar evidencia Plan 2, ocho objetos opacos y validación dirigida sin repetir integridad/decompilación.
- [x] Modos confirmados por el usuario para esta primera iteración: Arena, deathmatch, duelo por equipos, captura de bandera y cooperativo contra monstruos. 3A/3B/3C son partes obligatorias del mismo Plan 3, no iteraciones futuras.
- [ ] Revisión de diseño/subplanes y propuestas de capacidad/economía antes de ejecutar.

## Ejecución pendiente por entregas

- [ ] [3A — Arena jugable](./docs/superpowers/plans/2026-10-11-03a-arena-jugable.md): seleccionar IDs reales, convertir A1, menú/control/combate/oleadas/resultado, perfil local y primera aceptación.
- [ ] [3B — Tienda y multiplayer local](./docs/superpowers/plans/2026-10-11-03b-tienda-multiplayer-local.md): servidor headless, compra/equipo persistente, sala, deathmatch M1 y dos computadoras LAN.
- [ ] [3C — Modos y entrega](./docs/superpowers/plans/2026-10-11-03c-modos-y-entrega.md): M2, duelo por equipos, bandera/cooperativo, contenedor y aceptación de la matriz seleccionada.
- [ ] Futuro informe `./docs/analysis/resultado-plan-3.md`: pruebas propias del cliente/servidor, sin equiparar APK/C# a aceptación web.

## Restricciones vigentes

A1/M1/M2 son roles hasta vincularlos a fuentes; no son nombres de mapas recuperados. Catálogo conservado completo no implica conversión completa. Una entrada aplazada no bloquea el slice; una función crítica desconocida de una escena seleccionada sí. Los ocho objetos conservan motivo/evidencia por relevancia, sin exigir resolver contenido ajeno a esta iteración.

Consumir `./.lab/runs/20261011T174958Z-completion/` donde exista o recibir ubicación explícita. No repetir staging, hashes, auditoría de entradas, recuperación global ni preflights del Plan 2. Nuevas conversiones/evidencias en `./.lab/web-port/`, fuera de originales y privadas por defecto.

El servidor ahora aloja sala/simulación/API además del cliente. El navegador del host es un participante; otros equipos se unen por URL LAN. Ni dos pestañas locales ni un Dockerfile prueban acceso externo. Internet público, servicios originales, pagos, cuentas globales y móviles quedan fuera. No se cambian firewall/routing/certificados automáticamente.

La campaña permanece documentada para largo plazo. La siguiente iteración refina los mismos tres mapas; contenido adicional solo entra mediante lotes explícitos y aceptación propia.

## Contexto de los informes existentes

Según el informe enlazado del Plan 2, los cuatro proyectos/1.982 fuentes compilan; el inventario/exportación abarca todos los archivos y quedan ocho objetos con 332 bytes personalizados opacos. Hay 109 archivos de escena, no necesariamente 109 mapas. Tutorial/menú se probaron desde instalación limpia y Farm con perfil derivado; no se probó el multiplayer original. El proyecto Unity exportado no se compiló/ejecutó y no es requisito del port. Esas evidencias no se han vuelto a ejecutar al reformular estos planes.
