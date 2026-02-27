# Informe de cumplimiento — Mejora #3 (Homes y montajes)

Fecha: 2026-02-26

Resumen rápido
- Estado general: implementaciones parciales presentes para SSSD, PAM (pam_mount) y mapeo por grupos. Varias funciones generan archivos de configuración, pero faltan pasos de aplicación automática y ajustes para montajes per‑usuario seguros.

Hallazgos por componente

- `session_manager.py`
  - Declara modos `local`, `remoto`, `hibrido` y expone métodos: `configure_local()`, `configure_remoto()` (placeholder) y `configure_hibrido()` (devuelve config).
  - Gap: el modo `remoto` no implementa montaje ni validación; `hibrido` solo devuelve estructura config.

- `sssd_config.py`
  - Generador `SSSDConfigurator.generate_config()` devuelve plantilla con `override_homedir = /home/%{domain}/%{name}`.
  - `apply_config()` escribe usando `pkexec` y reinicia `sssd` (siempre que `pkexec` esté disponible).
  - Gap: no hay llamada central que obtenga la plantilla de `session_manager` y la aplique automáticamente tras unión.

- `pam_config.py`
  - `enable_pam_mount()` intenta insertar `pam_mount.so` en `common-session` y `generate_pam_mount_config()` escribe `pam_mount.conf.xml` vía `pkexec`.
  - Observación: la función puede devolver `None` cuando no hace cambios (usar retorno booleano consistente). La inserción actual es frágil (búsqueda por `pam_unix.so` simple).

- `network_mapper.py`
  - `GROUPS_CONFIG` contiene mapeos por grupos; `map_shares_for_groups()` y `generate_pam_mount_xml()` están implementados.
  - `generate_systemd_mounts()` produce unidades `.mount` pero sustituye `~` por `/etc/skel` (no expande al home real) y no escapa/normaliza nombres de unidad.

- `post_join_verifier.py`
  - Ejecuta comprobaciones (`realm`, `sssd`, `krb5.conf`) y llama a `PAMConfigurator` y `NetworkMapper` para generar `pam_mount`.
  - Gap: no coordina `HomeDirectoryManager` para aplicar `home_mode` ni llama a `SSSDConfigurator.apply_config()` con la plantilla de `session_manager`.

Riesgos y consideraciones de seguridad

- Creación/aplicación de config requiere `pkexec`/privilegios: asegurar flujo no interactivo en scripts automatizados o documentar el paso manual.
- No hay manejo de keytabs ni verificación de que Kerberos/realm tenga credenciales necesarias para montajes `sec=krb5i`.

Recomendaciones concretas (priorizadas)

1. Corregir `enable_pam_mount()` (`pam_config.py`) para devolver `True`/`False` consistente y robustecer la inserción en `common-session` (usar regex y respaldar el archivo antes de escribir).

2. Ajustar `generate_systemd_mounts()` (`network_mapper.py`):
   - No reemplazar `~` por `/etc/skel`. Generar plantillas que usen `Where=%h/Red/...` o crear unidades por usuario en runtime.
   - Normalizar/escapar nombres de unidad: usar `systemd-escape --path` o generar nombres basados en hash del path.

3. Implementar home remoto:
   - Opción A (recomendada): Generar `pam_mount` entry tipo `volume` para la ruta del home remoto (per‑usuario), y asegurar que `pam_mount` está habilitado y `keytab`/Kerberos listo.
   - Opción B: Crear systemd user automount units que monten en `%h` a demanda (recomendado para NFS autenticated via Kerberos si la infra lo soporta).

4. Integración post‑join:
   - `PostJoinVerifier.configure_post_join()` debe: aplicar plantilla SSSD (`SSSDConfigurator.apply_config()`), reiniciar `sssd`, esperar y luego aplicar `pam_mount` y generar/activar unidades systemd si procede.

5. Tests y ejemplos:
   - Añadir unidad de pruebas que genere ejemplos en `/tmp/edj_examples/` con: `sssd.conf` ejemplo, `pam_mount.conf.xml` generado para grupos de prueba, y muestras de `.mount`.
   - Añadir tests unitarios para `generate_pam_mount_xml()` y `generate_systemd_mounts()`.

Pasos siguientes que puedo ejecutar ahora

- (A) Implementar la corrección mínima en `enable_pam_mount()` y añadir pruebas rápidas. (rápido)
- (B) Ajustar `generate_systemd_mounts()` para usar `%h` y nombres seguros; generar ejemplos en `/tmp/edj_examples/`. (recomendado)
- (C) Integrar aplicación SSSD en `PostJoinVerifier` y generar un flujo completo de post‑join simulado. (más intrusivo)

Indica qué prefieres (A, B o C) y lo implemento. También puedo ejecutar primero las acciones no intrusivas (generar ejemplos en `/tmp/edj_examples`) para que revises las salidas.
