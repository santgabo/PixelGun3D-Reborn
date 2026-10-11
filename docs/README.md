# Convención de rutas

Las rutas de archivos del proyecto se escriben con `./` y se interpretan desde la raíz del repositorio, independientemente de la máquina o del nombre del worktree. Ejecutar los comandos desde esa raíz, salvo que el documento indique otro directorio; después de `cd ./web`, por ejemplo, `./src` se refiere a los archivos del cliente.

Ejemplos: `./docs/analysis/`, `./tools/prepare_unity_data.py` y `./.lab/runs/<corrida>/`. Las variables que representan ubicaciones del proyecto, como `RUN` y `MANAGED`, siguen la misma convención. No fijar rutas del equipo ni nombres de checkouts vecinos. Si las entradas privadas están en otro checkout, indicar su ubicación relativa al ejecutar.

Los enlaces Markdown se resuelven desde el documento que los contiene: usar `./archivo.md` para archivos del mismo directorio y `../` para subir directorios.

Las rutas internas de Android y del sistema operativo, como `/sdcard/Android/obb`, `/proc` o `/dev/kvm`, mantienen su forma original porque identifican ubicaciones del dispositivo o del sistema. Las URL de fuentes externas también se conservan.
