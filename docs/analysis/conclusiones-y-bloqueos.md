# Plan 2 — resultados y bloqueos

Corridas **20261009T191951Z** (estática) y **20261009T213202Z** (continuación dinámica autorizada), 2026-10-09 UTC. **Resultado general: PARTIAL.** El bloqueo de preparación se resolvió: dos arranques originales llegaron al tutorial offline y la cámara se comprobó en el segundo. Persisten cobertura de recursos y otras funciones no probadas.

Evidencias privadas en `.lab/runs/<corrida>/`, excluidas de Git. Resúmenes máquina: corrida estática `reports/resultados.json`, dinámica `reports/runtime-results.json`. La continuación instaló emulador/imagen con autorización expresa, **sin tocar firewall, grupos/KVM ni originales**. No se recompiló/firmó/modificó el juego, usaron cuentas personales ni habilitó Internet. Sin commits ni delegación.

## Cobertura real

| Tarea | Estado | Evidencia / límite |
|---|---|---|
| 1 — Entradas | PASS | 10.393 archivos / 1.977.291.055 bytes; ZIP/OBB/APK identificados. APK: 633 miembros, OBB: 9.758; cero diferencias/faltantes/sobrantes frente a unpacked. Identidad com.pixel.gun3d 11.3.1/1191 revalidada. |
| 2 — Mono | PASS acotado | Cuatro ensamblados, 1.982 archivos C#, ocho comandos rc0, cero diagnósticos detectados. Tres métodos contrastados con IL; no corrección global ni compilabilidad certificadas. |
| 3 — Staging | PASS acotado | 9.214 archivos, 176 grupos/766 fragmentos, 175 cabeceras serializadas consistentes y un FSB5. Fuentes/hash trazables y pruebas sintéticas RED→GREEN. Sin validación semántica global. |
| 4 — Recursos | PARTIAL | Cinco archivos / 3.524 objetos; 659 errores de lectura. Textura, audio y malla técnicamente validados; un MonoBehaviour enlazado al script y campo nativo. 8.160 archivos serializados pendientes; sin revisión perceptual ni layouts personalizados. |
| 5 — Android | PARTIAL | Apktool completo y JADX rc0; 4.253 Java, 717 anotaciones diagnósticas/257 archivos. Actividad/OBB/JNI definidos, ruta AppsMenu→Loading sustentada; primer menú y primera red efectiva no probados. |
| 6 — Runtime | PASS acotado | API25/Android7.1.1/x86 TCG; aislamiento/restauración/cuentas/ADB verificados. Dos originales al tutorial; rotación y avance del aviso en el segundo. Menú principal y lectura OBB trazada no probados. |
| 7 — Integridad/cierre | PASS acotado | Rehash también después de los ensayos dinámicos: 10.393 originales sin cambios/faltantes/extras; AVD restaurado y procesos cerrados. Informes saneados y evidencia privada. |

Herramientas utilizadas: Python 3.14.4, ILSpyCmd 11.1.0.9782/.NET del lock, UnityPy 1.25.4, AssetRipper Free 2.0.0, Temurin 21.0.12.1+1-LTS, JADX 1.5.6 y Apktool 3.0.3. Versiones/ayudas/comandos/stdout/stderr/rc efectivos están en `RUN/logs/`. Estas versiones/evidencias corresponden al análisis estático. La continuación usó Emulator 37.2.12.0, AOSP API25/x86 r1, ADB 37.0.1, Command-line Tools 17.0 y bubblewrap 0.11.1; perfiles/logs de cada ensayo en la corrida dinámica.

## Conclusiones graduadas

- **Confirmado:** preservación byte a byte de las entradas; equivalencia de los archivos desempaquetados con originales; decompilación de cuatro ensamblados; staging correcto por procedencia/cabeceras; muestras específicas decodificadas; enlace `level0:15 → globalgamemanagers.assets:750 → Assembly-CSharp.dll::DeviceOrientationMonitor`, `m_Enabled=1`.
- **Confirmado estáticamente:** actividad `com.prime31.UnityPlayerNativeActivity` (superclase UnityPlayerActivity), esquema de búsqueda del OBB 1191, puentes JNI y lista BuildSettings. Referencias: [mapa](mapa-dependencias.md), [inventario](inventario-recursos.md), [flujo](flujo-arranque.md).
- **Inferido:** AppCenter como escena inicial esperada y Loading como transición condicionada; acoplamiento Unity/backend y candidatos muy pequeños de lógica aislable. No son observaciones de ejecución.
- **Confirmado dinámicamente:** proceso/actividad, lógica Unity/Mono y tutorial 3D en dos referencias originales; bytes del OBB recuperado idénticos; rotación de cámara y paso al siguiente aviso de tutorial en la segunda. Namespace externo denegado, ADB operativo, Accounts0 y restauración limpia. [Hitos y evidencia](ejecucion-controlada.md).
- **No probado:** lectura OBB trazada (solo presencia/hash), menú principal, movimiento/disparo o finalización del tutorial, otras funciones offline, disponibilidad de servicios, fidelidad completa o viabilidad de portado sin Unity.

## Bloqueos ordenados y siguiente prueba pequeña

| Prioridad | Bloqueo | Prueba propuesta, todavía no iniciada | Coste relativo |
|---|---|---|---|
| Resuelto | Preparación runtime | Completada sin firewall ni administración: boot/ABI/egress/ADB/restauración y dos referencias originales. KVM sigue inaccesible, TCG funciona para este diagnóstico. | TCG lento/no soportado; no bloqueo actual |
| 1 | Type trees personalizados ausentes | Evaluar TypeTreeGeneratorAPI y probar solo `level0:16` con las DLL originales, contrastando un campo propio con AssetRipper. | Bajo/medio; dependencia nueva |
| 2 | PlayerSettings fuera de límites | Contrastar un campo/offset de `globalgamemanagers:1` con el parser de AssetRipper. El lector Python puro ya reprodujo fallo, sin corregirlo. | Bajo; diagnóstico puntual |
| 3 | Menú y funciones posteriores al tutorial | Proponer siguiente prueba pequeña offline de movimiento/disparo/progreso desde la misma plantilla, sin abrir servicios. Inicio ya reproducido; orden completo SDK/escenas no instrumentado. | Bajo/medio; no iniciado |
| 4 | Catálogo pendiente | Inventariar un lote explícito de archivos necesarios para esa escena/pregunta, sin exportar masivamente los 8.160 pendientes. | Variable; controlable por lote |

No se activará Internet, parcheará el manifiesto, alterarán licencias/compras ni sustituirán referencias para quitar un bloqueo. Frida/Ghidra siguen fuera de alcance salvo futura pregunta y autorización concreta.

## Decisiones históricas del análisis estático y sus costes

Las decisiones 1–9 siguientes describen `20261009T191951Z`; la autorización nueva y la resolución del runtime **no reescriben su historial**. Las decisiones de la continuación están en el ledger y [preparación/reversión](../lab/preparacion-runtime.md): SDK local independiente, aislamiento bubblewrap sin firewall, TCG observado, metadata oficial SDKmanager, locks propios fuera de la plantilla y permiso mínimo de almacenamiento.

1. Entradas y ejecutables del checkout vecino **solo lectura**; salidas/caches en este worktree. Coste si la vinculación no es portable: revalidar rutas/entorno al repetir.
2. **Sin commits ni subagentes**, según la restricción del plan. Coste: cambios sin commit y autorrevisión más débil que revisión independiente.
3. Briefs extraídos literalmente de `Tarea`, porque task-start reconoce solo `Task`. Coste: cotejo manual con el plan original.
4. Suite histórica de preflight no tratada como prueba actual: falla `Task1Preflight.setUpClass` por `.lab/private/input-baseline.json` ausente y exige herramientas no instaladas, estado ya obsoleto. Se conserva sin modificar; suite actual independiente. Coste: tests históricos no ejecutables en este worktree.
5. Context7 no instalado: `npx --no-install` lo rechazó; no se instaló. Ayudas/APIs instaladas y documentación oficial usadas en su lugar. Coste: diferencias de versión requieren contraste local (realizado).
6. ILSpyCmd ignoró selección `-m/-t` bajo `-il`: conservado IL completo del ensamblado y extraídos métodos por identidad/líneas/RVA. Coste: logs privados mayores y selección auditada separadamente del comando.
7. Piloto limitado a cinco archivos; AssetRipper recibió copias independientes del mismo conjunto con Managed, no una importación masiva. Coste: 7.999 dependencias omitidas en su piloto; no equivalen a corrupción y no certifican referencias globales.
8. Reordenamiento acotado: staging se preparó mientras se documentaba el análisis Mono; Android se decodificó después de obtener APK/identidad. Ningún consumidor avanzó sin sus entradas verificadas. Coste: el ledger, no el orden de narración, es la referencia de ejecución.
9. RUNTIME_READY no aprobado: tarea 6 detenida y cierre con NOT_RUN/BLOCKED. Coste: no se respondió aún si el juego arranca; no se convirtió el bloqueo previo en fallo del APK.

## Siguiente decisión

Recomendación: **preservar el APK original con Unity embebido y especificar gradualmente su comportamiento offline**, aprovechando el laboratorio ya comprobado. Todavía no hay evidencia que justifique una reimplementación completa ni cambios de servidores. Esta propuesta no inicia la fase siguiente.

Revisión final: autorrevisión contra los cinco focos del plan, sin delegación por restricción explícita. Rama `step/decompile` y worktree preservados, sin merge/push/commit. Los logs originales, código recuperado y exports no se publican.
