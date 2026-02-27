# Arquitectura - comprobación actual

El requisito solicitado enumeraba la siguiente estructura bajo `escuela-domain-joiner/`:

```
DEBIAN/
usr/
  bin/
  lib/escuela-domain-joiner/
    ... módulos (
      domain_discovery.py,
      ...
      pam_config.py, sssd_config.py, etc.)
  share/
    aplicaciones, icons y un directorio `escuela-domain-joiner/` con:
      templates/ (sssd.conf.template, krb5.conf.template, ...)
      examples/ (config yml)
etc/escuela-domain-joiner/config.yml
var/lib/escuela-domain-joiner/...
```

## Encontrado en el workspace

- **DEBIAN/** existe con `control` y `postinst`.
- **usr/lib/escuela-domain-joiner/** contiene los módulos principales: 
  `logger.py`, `domain_*`, `session_manager.py`, `network_mapper.py`, 
  `backup_restore.py`, `post_join_verifier.py`, `pam_config.py`, 
  `sssd_config.py`, `kerberos_config.py`, `samba_config.py`, `exceptions.py`.
- **usr/sbin/** tiene `edj-verify-domain` (script de verificación).
- No aparece un directorio `usr/share/escuela-domain-joiner` en el repositorio;
  sólo existen `usr/share/applications`, `usr/share/icons`.
- Las plantillas y ejemplos mencionados no están en el árbol de fuentes.
  Sólo hay backups temporales en `tmp_sim/backups/templates` generados por pruebas.
- En el workspace hay `etc/` y `var/` sólo en el layout de la estructura de la
  tarea pero no contienen archivos reales (no están dentro del repo).

## Gap detectados

1. **Faltan las plantillas (`*.template`) y ejemplos (`config-*.yml`).**
   No hay evidencia de haberlas introducido en el proyecto. Necesario para
   generar configuraciones SSSD/Kerberos/PAM/samba según la arquitectura.
2. El directorio `usr/share/escuela-domain-joiner/...` no está presente.
3. **Ejemplos generados**: existe un script `tools/generate_examples_mejora3.py`
   que produce `/tmp/edj_examples`, pero esos archivos no se incorporaron al
   repositorio.

## Añadidos recientes

- Se han creado los subdirectorios `usr/share/escuela-domain-joiner/templates`
  y `examples` con contenidos mínimos para los archivos requeridos.
- El `postinst` pasa a copiar estos recursos y a establecer permisos.
- Se agregaron tests que comprueban la presencia de dichos ficheros.
- Se introdujo un sistema de logging mejorado en `logger.py` que expone cuatro
  loggers separados (`install`, `auth`, `access`, `errors`) y maneja rotación
  de archivos. Esto cumple el requisito de múltiples logs con distintas
  retenciones.
- Se implementaron los comandos de diagnóstico `edj-status`,
  `edj-test-domain`, `edj-remount-shares` y `edj-diagnose`; existen y son
  ejecutables, con tests que los verifican.

## Conclusión

La mayoría de los componentes de la librería están implementados y probados
(incluyendo las mejoras #2 y #3). Sin embargo la parte de datos estáticos
(plantillas y ejemplos) no se encuentra en el árbol. Si la arquitectura debe
ser exacta, hace falta añadir los ficheros bajo `usr/share/escuela-domain-joiner/
templates` y `examples` y posiblemente un `etc/escuela-domain-joiner/config.yml`.

## Recomendaciones

- Añadir las plantillas comentadas y ejemplos de configuración de dominio
  en el repo para completar la estructura.
- Actualizar `DEBIAN/postinst` si necesita instalar esos datos en tiempo de
  empaquetado.
- Verificar que `tests/` incluyan comprobaciones que detecten la presencia de
  estos recursos en futuras ejecuciones.
