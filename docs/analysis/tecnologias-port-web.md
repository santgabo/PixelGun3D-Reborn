# Investigación tecnológica — port web sin Unity

Fecha: 2026-10-10. **Estado: stack recomendado aprobado por el usuario; investigación conservada como fundamento.** El usuario solicitó documentar el plan sin implementar en esta sesión. Véanse el [diseño](../superpowers/specs/2026-10-10-03-port-web-sin-unity-design.md) y el [Plan 3](../superpowers/plans/2026-10-10-03-reimplementacion-web-single-player.md); sus criterios detallados quedan para revisión previa a ejecución.

**Cambio de alcance 2026-10-11:** el usuario solicitó un slice de tres mapas con Arena, tienda y multiplayer real propio. El diseño/Plan 3 enlazados arriba sustituyen las restricciones históricas de cobertura completa y servicios dummy de esta investigación. El fundamento del cliente se conserva; servidor Node/TypeScript/WebSocket y contenedor son propuestas nuevas cuya compatibilidad/paquetes se validan en 3B.1, no conclusiones de esta investigación anterior.

## 1. Alcance histórico de la investigación

- Reimplementación sin Unity Editor, runtime Unity ni exportación Unity WebGL.
- Navegadores de escritorio; móviles fuera de esta iteración.
- Linux headless sirve archivos por HTTP; una MacBook en la LAN descarga y ejecuta el juego usando su propia CPU/GPU.
- Prioridad: escenas, menús, conservación de mapas, single player, fidelidad, estabilidad y fluidez.
- Servicios dummy locales; sin reconstrucción del multiplayer ni dependencia de servidores originales.
- Se acepta la evidencia del Plan 2. **No repetir hashes, comparaciones de entradas ni pruebas de integridad.** Las comprobaciones nuevas propuestas son del funcionamiento de la reimplementación.

La extracción/conversión con herramientas externas que leen los formatos originales no implica incorporar Unity al producto ni utilizar su editor.

## 2. Recomendación

**TypeScript + Babylon.js convencional + WebGL 2 + Havok WASM, con Vite para construir el cliente.** Menús/HUD inicialmente en HTML/CSS usando los recursos originales; escenas y modelos convertidos a glTF/GLB y datos específicos del juego en manifiestos JSON.

Esta selección busca reducir infraestructura que habría que escribir y depurar. **No es una afirmación de que Babylon sea universalmente más rápido**: no se han ejecutado benchmarks del juego con ninguno de los candidatos.

La recomendación es Babylon.js convencional, no Babylon Lite. El índice documental consultado mezcla ejemplos de ambos; no deben mezclarse sus APIs ni elegir una variante exclusiva de WebGPU para un requisito de HTTP remoto.

## 3. Comparación de candidatos

| Candidato | Ventaja para este proyecto | Coste/riesgo | Decisión propuesta |
|---|---|---|---|
| **Babylon.js** | Grafo de escenas, animación, audio, materiales, inspección y soporte de física/Havok y controlador de personaje. WebGL y WebGPU disponibles. | Aprender sus ciclos de vida; evitar dependencias implícitas de CDN; adaptar materiales y comportamiento original. | **Primera opción**, por cobertura y menor integración propia. |
| **Three.js + Rapier** | Gran control del renderizador y pipeline; Rapier aporta física WASM y controlador cinemático. | Three.js no es un motor de juego completo. Debemos integrar estados, input, física, eventos y gestión de vida de recursos; mayor superficie de fallos. | Alternativa sólida si controlar el renderizador prima sobre reducir infraestructura. |
| **PlayCanvas Engine standalone** | Motor orientado a juegos con entidades/componentes, WebGL/WebGPU y física Ammo. Puede usarse sin editor alojado. | También necesita conversión de escenas y reconstrucción de gameplay. No hay evidencia local que demuestre una ventaja decisiva sobre Babylon. | Segundo motor completo a considerar; no descartarlo por una supuesta obligación de usar la nube. |
| **Godot Web** | Editor y motor completos, exportación web WASM/WebGL 2. | Otra migración de proyecto; restricciones de exportación y advertencias específicas para Safari. La documentación estable consultada no permite exportar proyectos Godot 4 C# a web. | No preferido para una reimplementación exclusivamente web. |
| **Motor propio Rust/C++ → WASM** | Control de simulación y subsistemas intensivos. | Exige construir/integrar mucho más; WASM no resuelve escenas, UI ni compatibilidad de motor. | No justificado para esta iteración. |

Fuentes: capacidades Babylon [1–3], alcance Three.js [4], Rapier [5–6], PlayCanvas [7–8], Godot [9]. El orden es un juicio de ingeniería para este alcance, no un ranking universal.

## 4. WebAssembly, WebGL y WebGPU no son alternativas equivalentes

- **WebGL 2 / WebGPU:** APIs gráficas usadas por el motor para acceder a la GPU.
- **Babylon / Three / PlayCanvas:** bibliotecas o motores que estructuran y renderizan contenido.
- **WebAssembly:** formato de ejecución para módulos compilados; complementa JavaScript. No sustituye por sí mismo al motor gráfico [10].

Uso recomendado de WASM: física existente, y decodificadores cuando el formato de recursos lo requiera. Mantener gameplay, UI y estados en TypeScript; considerar módulos propios WASM solo si un perfil futuro identifica un cuello de botella concreto.

Compilar o alojar el C# recuperado no reproduce las APIs, física, coroutines, serialización ni ciclo de vida de Unity. El código recuperado sirve como referencia de comportamiento, no como cliente web ejecutable.

### Física: Havok frente a Rapier

**Havok es el candidato inicial con Babylon** porque cuenta con integración oficial y controlador de personaje [2–3]. Su distribución web consultada es WASM bajo MIT y requiere SIMD; deberán definirse navegadores de escritorio compatibles. No se presupone que reproduzca exactamente el CharacterController o la física del original.

**Rapier** es una buena alternativa, especialmente con Three.js. Sus bindings JavaScript usan WASM y disponen de controlador de personaje [5–6]. Con Babylon habría que asumir una integración propia en vez de dar por existente un plugin oficial equivalente al de Havok.

No incorporar ambos motores a la primera versión. El movimiento requiere ajustar gravedad, velocidad, escalones, pendientes, salto y colisiones según el comportamiento del juego, con independencia del motor elegido.

## 5. Restricción decisiva: HTTP remoto en LAN

`http://192.168.x.x:puerto` no recibe la excepción de origen confiable de `http://localhost`: localhost se refiere a la máquina donde se ejecuta el navegador [11].

Consecuencias:

1. **WebGL 2 será el backend requerido de esta iteración.** Detectar capacidad y mostrar un error útil si no está disponible; no prometer compatibilidad con cualquier GPU o navegador histórico.
2. **No exigir WebGPU**, porque requiere contexto seguro [12]. Puede evaluarse en una fase posterior con HTTPS confiable; no aporta una razón para cambiar ahora el requisito HTTP.
3. **No exigir WASM multihilo/SharedArrayBuffer**: compartir memoria requiere contexto seguro y aislamiento cross-origin [13]. Agregar COOP/COEP no convierte por sí solo HTTP remoto en un contexto seguro.
4. WASM sin memoria compartida y workers ordinarios con mensajes no son lo mismo que WASM multihilo. Evitar una dependencia de memoria compartida no implica renunciar a todo WASM ni a todos los workers.
5. No depender de service workers/PWA para arrancar o cargar mapas; su registro exige contexto seguro [11]. Se puede utilizar caché HTTP convencional.
6. No pedir flags que desactiven la seguridad del navegador como parte del procedimiento normal.

El servidor no necesita pantalla o GPU para **servir** el cliente. La eventual automatización de navegadores en Linux tiene requisitos diferentes y no sirve por sí sola como medida de la fluidez en la MacBook.

## 6. Arquitectura candidata

```text
Linux headless — servidor HTTP estático
    ├── HTML/CSS/JS del cliente
    ├── módulos WASM y decodificadores locales
    └── recursos por escena + manifiestos
                 │ HTTP por LAN
                 ▼
MacBook — navegador
    ├── UI y estados del juego (TypeScript + HTML/CSS)
    ├── escenas/renderizado (Babylon.js + WebGL 2)
    ├── física (Havok WASM)
    ├── gameplay single player
    └── servicios dummy + guardado local
```

### Recursos y conservación

- Reutilizar geometría, texturas, audio y animaciones recuperables; no reemplazar mapas por aproximaciones de apariencia similar.
- glTF/GLB para representación gráfica; JSON complementario para identidad, jerarquía necesaria, spawn points, triggers, colisiones y comportamiento. **Un GLB no conserva automáticamente una escena Unity completa.**
- Conversión explícita de ejes, unidades, orientación de caras, transformaciones, UV, materiales, transparencia y lightmaps. Evitar doble conversión de coordenadas.
- Mantener la apariencia original; no transformar indiscriminadamente materiales heredados en PBR, ni sustituir iluminación horneada por iluminación moderna que cambie el aspecto.
- Cargar recursos por escena y compartir recursos comunes; no descargar y mantener todo el contenido original al entrar al menú.
- Evaluar instancias, culling, texturas KTX2 y compresión de mallas donde reduzcan costes sin degradar la fidelidad. No aplicar compresión con pérdida indiscriminadamente a atlases/UI.
- Alojar loaders, WASM y decodificadores en el propio servidor. La documentación del loader Babylon advierte que algunas extensiones usan decodificadores desde CDN por defecto [14].

### Menús, estados y estabilidad

- HTML/CSS para menús y HUD como propuesta inicial: reutilizar sprites/atlases y reconstruir anclajes, escala y navegación originales, sin rediseñar la interfaz por conveniencia.
- Separar estados de menú, carga, partida, pausa y error; no permitir que una transición deje dos partidas o bucles activos.
- Liberar escenas, recursos físicos, audio, suscripciones y tareas al salir. Cargas cancelables, errores visibles y posibilidad de volver al menú.
- Paso fijo de simulación con límite de recuperación tras pausas; renderizado independiente. Tratar pérdida de foco, retorno a pestaña y pérdida de contexto gráfico.
- Activación de audio y captura de ratón desde interacción del usuario; probar Escape, pausa y recuperación de input en los navegadores objetivo.
- Dummy detrás de interfaces pequeñas: perfil local, progreso, configuración y disponibilidad online. Ninguna llamada al backend original; funcionalidades online deshabilitadas explícitamente, no falsamente exitosas.
- Guardado local con versión y manejo de almacenamiento denegado o agotado; no bloquear el arranque por un error de persistencia.

Son propuestas de diseño, no funciones ya implementadas ni promesas de fidelidad demostrada.

### Construcción y alojamiento

Vite produce una distribución estática. El servidor de la LAN debe servir **solo esa distribución y los recursos necesarios**, no el repositorio, decompilados, originales ni `.lab`. No se necesita SSR, una base de datos ni un servidor de gameplay para esta iteración.

`vite preview` es una herramienta de previsualización, no el servidor de producción recomendado [15]. La herramienta HTTP concreta y el puerto se decidirán en el diseño; no se modifica firewall ni se abren servicios durante esta investigación.

## 7. Verificación de la futura versión, no auditoría del original

- Automatización funcional del nuevo cliente con Playwright: navegación, carga de mapas, reinicio, pausa, retorno al menú y errores de consola/red.
- Playwright en Chromium/Firefox/WebKit ayuda a detectar regresiones. **Su WebKit no es Safari de marca**; no reemplaza probar Safari en la MacBook [16].
- Verificación real desde la MacBook por LAN: renderizado, controles, audio, fidelidad, tiempos de carga y tiempos de frame. Linux headless no certifica el rendimiento de macOS.
- Proponer una meta inicial de **60 fps a resolución interna 1920×1080**, pendiente del modelo de MacBook, navegador y escenas representativas. Medir distribución de tiempos de frame, cargas frías/calientes y evolución de memoria, no solo FPS medios. Evitar renderizar automáticamente a toda la resolución Retina sin presupuesto.
- Definir una duración de sesión y un número de ciclos de cambio de mapa para aceptar estabilidad. No prometer ausencia absoluta de crashes en cualquier condición; sí exigir cero fallos observados en una matriz y recorrido documentados.
- Empezar por un recorrido representativo completo —menú → mapa original → movimiento/colisiones/disparo → pausa → menú— y después ampliar cobertura. Ese primer recorrido es una puerta de avance, no un sustituto de conservar el resto del contenido acordado.

No se han ejecutado estos ensayos ni benchmarks. No se han vuelto a comprobar entradas del Plan 2.

## 8. Decisiones pendientes

1. **Resuelto:** stack aprobado; diseño y Plan 3 documentados, sin ejecución.
2. Modelo de MacBook y versiones efectivas de navegadores para confirmar presupuestos y matriz de aceptación definidos en el diseño.
3. Identificadores concretos del catálogo de menús/modos/mapas: tarea 1 del Plan 3, aprovechando las salidas existentes sin nueva auditoría de integridad.
4. El diseño incluye enemigos, objetivos, progresión y guardado de los modos single player; sus familias y parámetros se obtendrán del contenido, sin inventar comportamiento.

No se fijan números de versión por fama o por un comparativo externo. Al preparar el plan se elegirán versiones compatibles explícitas y un lockfile; esta investigación compara capacidades, no certifica una combinación instalada.

## 9. Fuentes oficiales consultadas

1. Babylon.js, capacidades: https://www.babylonjs.com/specifications/
2. Babylon, integración Havok/WASM/licencia/SIMD: https://github.com/BabylonJS/Documentation/blob/master/content/features/featuresDeepDive/physics/v2/usingHavok.md
3. Babylon, controlador: https://github.com/BabylonJS/Documentation/blob/master/content/features/featuresDeepDive/physics/v2/characterController.md
4. Three.js, alcance de biblioteca frente a motor: https://threejs.org/manual/pages/game.html
5. Rapier, JavaScript/WASM: https://rapier.rs/docs/user_guides/javascript/getting_started_js/
6. Rapier, controlador: https://rapier.rs/docs/user_guides/javascript/character_controller/
7. PlayCanvas standalone sin editor: https://developer.playcanvas.com/user-manual/engine/standalone/
8. PlayCanvas, física: https://developer.playcanvas.com/user-manual/physics/physics-basics/
9. Godot, exportación web y restricciones: https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html
10. MDN, WebAssembly: https://developer.mozilla.org/en-US/docs/WebAssembly
11. MDN, contextos seguros: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts
12. MDN, WebGPU: https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API
13. MDN, memoria compartida: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer
14. Babylon, glTF y decodificadores: https://github.com/BabylonJS/Documentation/blob/master/content/features/featuresDeepDive/importers/glTF.md
15. Vite, distribución estática: https://vite.dev/guide/static-deploy.html
16. Playwright, navegadores: https://playwright.dev/docs/browsers

Método: consulta Context7 y contraste directo con documentación oficial. Los ejemplos de Babylon Lite devueltos por Context7 no se usaron para justificar APIs del motor convencional. Las páginas Babylon de física devolvieron 404; se consultaron sus fuentes oficiales Markdown en GitHub. Los comparativos comerciales aparecidos en la búsqueda no sustentan afirmaciones de rendimiento de este informe.
