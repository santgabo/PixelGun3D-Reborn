# Continuación autorizada del Plan 2 — 2026-10-11

[Informe vigente y evidencias](./docs/analysis/continuacion-plan-2-2026-10-11.md).

- [x] Instalar y comprobar la suite local de recuperación y runtime.
- [x] Recuperar y autenticar APK/OBB originales sin modificarlos.
- [x] Decompilar los cuatro ensamblados y compilar juntos los scripts recuperados.
- [x] Inventariar todos los archivos Unity y exportar proyecto/recursos; conservar ocho objetos con campos opacos y tipos ausentes como bytes originales.
- [x] Recuperar Android completo en Smali y documentar Java/instrucciones alternativas.
- [x] Completar y documentar gameplay/tutorial/menú del original, repetir desde AVD limpio y cerrar procesos; comprobar Farm offline con perfil derivado separado.

# Preparación del Plan 3 — juego en navegador

[Convención de rutas relativas](./docs/README.md).

Seguimiento de planificación, no plan de implementación aprobado. No autoriza cambios al juego, instalaciones, commits ni ejecución del portado.

- [x] Clasificar el cambio como arquitectónico y revisar contexto, informes y commits recientes.
- [x] Confirmar plataforma: exclusivamente navegadores de escritorio; servidor Linux headless sirve el juego por HTTP a una MacBook en la LAN.
- [x] Confirmar reimplementación completamente sin Unity y realizar investigación documental de tecnologías web.
- [x] Stack aprobado por el usuario: TypeScript + Babylon.js convencional + WebGL 2 + Havok WASM.
- [x] Apoyo visual: no fue necesario para las decisiones tomadas.
- [x] Comparar motores web con evidencia técnica: `./docs/analysis/tecnologias-port-web.md`.
- [x] Documentar diseño, cobertura y presupuestos propuestos: `./docs/superpowers/specs/2026-10-10-03-port-web-sin-unity-design.md`.
- [x] Redactar por petición expresa el Plan 3 con writing-plans: `./docs/superpowers/plans/2026-10-10-03-reimplementacion-web-single-player.md`.
- [x] Autorrevisar documentos: cobertura, dependencias, contratos, aceptación y exclusión de nuevas pruebas de integridad.
- [x] Actualizar Plan 3 y diseño con las rutas recuperadas, límites de los ocho objetos y alcance real de las pruebas originales del 2026-10-11.
- [ ] Revisión del usuario de diseño/plan y criterios detallados antes de una futura sesión de ejecución.
- [ ] Autorización explícita de ejecución futura. **Prohibido implementar en esta sesión.**

## Pendientes incorporados al Plan 3

- [ ] Consumir `./.lab/runs/20261011T174958Z-completion/managed/rebuild/`, staging, inventario refinado y exports existentes como base de la conversión web; no repetir decompilación ni integridad del Plan 2.
- [ ] Catalogar los ocho objetos con referencias, impacto y evidencia: excluir los que se demuestren de Editor/servicios fuera de alcance; mantener `LpOwerride` sin atribución hasta investigarlo y resolver cualquier dato/comportamiento requerido por las escenas afectadas.
- [ ] Contrastar los layouts advertidos y adaptar shaders/medios para el runtime web; exportar no equivale a fidelidad o integración verificadas.
- [ ] Validar en el cliente web nuevo tutorial → menú → Campaign sin dependencia de la primera partida multijugador; no importar el perfil Android derivado.
- [ ] Completar las pruebas web de contenido, gameplay, estabilidad y rendimiento previstas; las pruebas del APK original y la compilación C# son referencias, no aceptación del port.

## Contexto verificado en los informes existentes

La recuperación y pruebas del Plan 2 se ampliaron por autorización nueva del 2026-10-11; su estado vigente está en el informe enlazado arriba. Las 1.982 fuentes de los cuatro proyectos C# compilan sin errores y están en `./.lab/runs/20261011T174958Z-completion/managed/rebuild/`; la lógica principal está en `Assembly-CSharp/`. El inventario/exportación abarca todos los archivos; quedan ocho objetos con 332 bytes personalizados sin interpretar. Hay 109 archivos de escena, no necesariamente 109 mapas. Las pruebas se hicieron con el APK original: tutorial/menú desde instalación limpia y Farm con perfil derivado. El proyecto Unity exportado no se compiló ni ejecutó; el Plan 3 sigue siendo una reimplementación sin Unity y requiere sus propias pruebas.

## Prioridad y restricciones expresadas por el usuario

Reimplementación completamente sin Unity Editor ni runtime Unity. Ejecución fluida exclusivamente en navegadores de escritorio, independientemente del sistema operativo. Escenas y menús que carguen correctamente, mapas conservados y single player sin crashes. La validación de fidelidad, estabilidad y rendimiento se concentra en el propio juego, no en las conexiones en línea. Servicios originales sustituidos temporalmente por un dummy; multiplayer funcional y navegadores móviles fuera de esta iteración.

Despliegue esperado: servidor Linux headless accesible por HTTP desde una MacBook conectada a la misma LAN. El juego debe ejecutarse en el navegador de la MacBook; no se presupone pantalla ni renderizado remoto en el servidor. Este escenario debe formar parte de la aceptación, no limitarse a localhost.

En la futura ejecución del Plan 3 no repetir las verificaciones de entradas del Plan 2; aceptar su evidencia documentada como base. La continuación actual del Plan 2 fue autorizada expresamente por el usuario y responde a los huecos de recuperación y runtime anteriores. Las pruebas propias del Plan 3 se centrarán en el funcionamiento y rendimiento de la versión web.

