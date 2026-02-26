Pruebas en máquina real — Escuela Domain Joiner v2.0

Este documento resume los pasos básicos para validar la Mejora #2 (Verificación post-reinicio) en una máquina real con `realm`/`sssd` instalados.

Resumen rápido:
- Instalar paquete .deb
- Crear `pending_verify` con `domain=...`
- Reiniciar y responder diálogo SÍ/NO
- Verificar plantillas en `/var/lib/escuela-domain-joiner/backups/templates/`
- Verificar reportes en `/var/lib/escuela-domain-joiner/backups/reports/`

Para el procedimiento completo y comandos exactos, consulta `README_TESTING.md` en la raíz del proyecto.
