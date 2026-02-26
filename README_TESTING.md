# Pruebas en máquina real — Escuela Domain Joiner v2.0

Este documento contiene pasos exactos para validar la Mejora #2 (Verificación post-reinicio) en una máquina real con `realm`/`sssd` instalados.

PRECAUCIONES
- Ejecuta las pruebas en un equipo de laboratorio o VM. Evita usar equipos de producción.
- Requiere privilegios `root` para restauraciones y reinicios de servicios.
- Asegúrate de tener una copia de seguridad completa de la VM antes de probar rollback.

Resumen de pasos
1. Instalar paquete `.deb` (o usar el árbol de trabajo).
2. Simular unión (o unir al dominio real) desde la GUI.
3. Reiniciar la máquina y responder el diálogo SÍ/NO.
4. Verificar artefactos: plantillas y reportes.

Comandos: instalación y preparación
```bash
# Instalar paquete (si lo tienes generado)
sudo dpkg -i escuela-domain-joiner.deb
sudo systemctl daemon-reload
sudo systemctl enable edj-verify-domain.service

# Asegurarse de directorios
sudo mkdir -p /var/lib/escuela-domain-joiner/backups
sudo chown -R $USER:$USER /var/lib/escuela-domain-joiner
```

Crear marcador `pending_verify` (simulación previa al reinicio)
```bash
# Desde la máquina 'post-join' (ej: después de realm join exitoso)
echo -e "domain=escuela.local\ntimestamp=$(date +%Y%m%d%H%M%S)" | sudo tee /var/lib/escuela-domain-joiner/pending_verify
```

Forzar ejecución del script (sin reiniciar) — útil para pruebas interactivas
```bash
sudo /usr/sbin/edj-verify-domain
```

Flujo A — Usuario responde SÍ (éxito)
1. Asegúrate de que `/var/lib/escuela-domain-joiner/pending_verify` existe y contiene `domain=...`.
2. Ejecuta el script: `sudo /usr/sbin/edj-verify-domain`.
3. En el diálogo, selecciona `SÍ`.

Verificaciones post-ÉXITO
- El marcador debe eliminarse:
  - `ls -l /var/lib/escuela-domain-joiner/pending_verify` → no debe existir.
- Se debe crear una plantilla en:
  - `/var/lib/escuela-domain-joiner/backups/templates/template_<domain>_<ts>.tar.gz`
  - `ls -l /var/lib/escuela-domain-joiner/backups/templates/`

Flujo B — Usuario responde NO (rollback)
1. Con `pending_verify` presente, ejecuta el script: `sudo /usr/sbin/edj-verify-domain`.
2. En el diálogo, selecciona `NO`, y luego confirma "¿Desea deshacer la unión?".

Qué ocurre en rollback
- Se busca el backup más reciente `prejoin_*.tar.gz` en `/var/lib/escuela-domain-joiner/backups/` y se extrae.
- Se intentará ejecutar `realm leave <domain>` (requiere `realm` instalado y privilegios).
- Se reiniciarán servicios: `sssd` y `realmd`.
- Si algo falla, el sistema generará un reporte en:
  - `/var/lib/escuela-domain-joiner/backups/reports/error_report_<ts>.txt`

Verificaciones post-ROLLBACK
- Comprueba que los archivos originales han sido restaurados:
  - `sudo journalctl -u sssd --no-pager | tail -n 50`
  - `sudo systemctl status sssd realmd`
- Si el rollback generó un reporte:
  - `ls -l /var/lib/escuela-domain-joiner/backups/reports/`
  - `cat /var/lib/escuela-domain-joiner/backups/reports/error_report_<ts>.txt`

Logs y diagnóstico
- Para ver el output del servicio en systemd:
```bash
sudo journalctl -u edj-verify-domain.service --no-pager
```
- Ver los últimos 200 líneas del journal general (útil para problemas de kerberos/sssd):
```bash
sudo journalctl -n 200 --no-pager
```

Sugerencias de prueba adicional
- Prueba el flujo SÍ/NO tanto con unión real (realm join) como simulada (crear `pending_verify`).
- Forzar fallos: renombra temporalmente `/etc/sssd/sssd.conf` antes de rollback para forzar errores y comprobar que se genera `error_report`.

Preguntas frecuentes / Problemas conocidos
- El script usa `tkinter` para el diálogo; en despliegues sin servidor X, el servicio debe ejecutarse en sesión gráfica o usar fallback (zenity). Si necesita fallback, puedo añadirlo.
- `realm leave` y `systemctl restart` requieren privilegios: la ejecución automática por systemd debe correr con los permisos adecuados o el script debe invocar `pkexec`/sudo según la política.

¿Quieres que además cree un `README.md` reducido dentro del paquete (`/usr/share/doc/escuela-domain-joiner/README.md`) con estos pasos?