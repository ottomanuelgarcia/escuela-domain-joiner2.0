# Referencias y estándares utilizados

El desarrollo de *Escuela Domain Joiner* se apoya en varios proyectos y
especificaciones de la industria. A continuación se enumeran las fuentes más
relevantes que se consultaron o cuyas APIs se consumen directamente:

- **Microsoft Active Directory Domain Services**
  - Documentación oficial de AD DS para la administración de dominios, OU,
    permisos y proveedores LDAP/AD.
- **Samba 4.x Documentation**
  - Guías de configuración de `smb.conf`, `winbind` y compatibilidad con AD.
- **SSSD (System Security Services Daemon) Documentation**
  - Manual de `sssd.conf`, respaldo de home directories y overrides.
- **FreeIPA/IdM Integration Guide**
  - Para entender el funcionamiento de `realm join` y la interoperabilidad
    con entornos IPA/AD.
- **Debian Policy Manual**
  - Requisitos de empaquetado en `/DEBIAN/control`, `postinst`, dependencias
    y estándares de rutas de sistema.
- **Python 3.8+ Documentation**
  - Uso de `subprocess`, `logging`, `importlib`, y compatibilidad de sintaxis.
- **Tkinter 8.6 Documentation**
  - API utilizada para la interfaz gráfica y los diálogos `askyesno`.

El código fuente incluye comentarios y metadatos (por ejemplo, `DEBIAN/control`
que lista dependencias como `python3 (>= 3.8)`, `python3-tk`, `sssd`,
`samba-common-bin`, etc.) que evidencian estas referentencias.

Además, diversos módulos mencionan explícitamente `Active Directory`, `SSSD`,
`Samba` y `Tkinter` en sus docstrings y comentarios de cabecera. Los tests y los
scripts de verificación también dependen de la terminología y funciones de
estas tecnologías.
