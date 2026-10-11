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
- [ ] Revisión del usuario de diseño/plan y criterios detallados antes de una futura sesión de ejecución.
- [ ] Autorización explícita de ejecución futura. **Prohibido implementar en esta sesión.**

## Contexto verificado en los informes existentes

Los planes anteriores cerraron sus actividades, pero el resultado técnico del Plan 2 sigue siendo PARTIAL: tutorial y cámara observados; menú principal y gameplay completo no certificados. Hay 109 archivos de escena, no necesariamente 109 mapas. La recuperación de recursos aún tiene cobertura parcial y errores de lectura pendientes.

## Prioridad y restricciones expresadas por el usuario

Reimplementación completamente sin Unity Editor ni runtime Unity. Ejecución fluida exclusivamente en navegadores de escritorio, independientemente del sistema operativo. Escenas y menús que carguen correctamente, mapas conservados y single player sin crashes. La validación de fidelidad, estabilidad y rendimiento se concentra en el propio juego, no en las conexiones en línea. Servicios originales sustituidos temporalmente por un dummy; multiplayer funcional y navegadores móviles fuera de esta iteración.

Despliegue esperado: servidor Linux headless accesible por HTTP desde una MacBook conectada a la misma LAN. El juego debe ejecutarse en el navegador de la MacBook; no se presupone pantalla ni renderizado remoto en el servidor. Este escenario debe formar parte de la aceptación, no limitarse a localhost.

No realizar nuevas pruebas de integridad ni repetir las verificaciones de entradas del Plan 2. Su evidencia documentada se acepta como base. Las limitaciones conocidas de recuperación siguen siendo contexto de implementación, no una autorización para reabrir la auditoría. Las pruebas nuevas se centrarán en el funcionamiento y rendimiento de la versión web.

