# Convención de rutas

Las rutas de archivos del proyecto se escriben con `./` y se interpretan desde la raíz del repositorio, independientemente de la máquina o del nombre del worktree. Ejecutar los comandos desde esa raíz, salvo que el documento indique otro directorio; después de `cd ./web`, por ejemplo, `./src` se refiere a los archivos del cliente.

Ejemplos: `./docs/analysis/`, `./tools/prepare_unity_data.py` y `./.lab/runs/<corrida>/`. Las variables que representan ubicaciones del proyecto, como `RUN` y `MANAGED`, siguen la misma convención. No fijar rutas del equipo ni nombres de checkouts vecinos. Si las entradas privadas están en otro checkout, indicar su ubicación relativa al ejecutar.

Los enlaces Markdown se resuelven desde el documento que los contiene: usar `./archivo.md` para archivos del mismo directorio y `../` para subir directorios.

Las rutas internas de Android y del sistema operativo, como `/sdcard/Android/obb`, `/proc` o `/dev/kvm`, mantienen su forma original porque identifican ubicaciones del dispositivo o del sistema. Las URL de fuentes externas también se conservan.

## Planificación vigente del juego web

- [Diseño del slice](./superpowers/specs/2026-10-10-03-port-web-sin-unity-design.md).
- [Plan 3 — índice y contratos](./superpowers/plans/2026-10-10-03-reimplementacion-web-single-player.md): tres mapas, menú/tienda, Arena y multiplayer propio.
- [3A — Arena jugable](./superpowers/plans/2026-10-11-03a-arena-jugable.md).
- [3B — Tienda y multiplayer local](./superpowers/plans/2026-10-11-03b-tienda-multiplayer-local.md).
- [3C — Modos y entrega en contenedor](./superpowers/plans/2026-10-11-03c-modos-y-entrega.md).
- [Roadmap pendiente, sin planes numerados](./superpowers/pendientes/roadmap.md): refinamiento primero, mapas por lotes después, campaña a largo plazo.

La revisión del 2026-10-11 reemplaza el alcance anterior de port completo/single player. Los informes del Plan 2 conservan su valor histórico; no son aceptación de la implementación web.
