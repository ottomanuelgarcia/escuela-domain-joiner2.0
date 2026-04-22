# Informe de Errores y Sugerencias - Escuela Domain Joiner

Este documento detalla los problemas encontrados y las áreas de mejora identificadas en el proyecto `escuela-domain-joiner`.

## 1. Inconsistencias de Idioma y Metadatos
*   **Mezcla de Idiomas:**
    *   `DEBIAN/control`: Contiene descripciones en portugués, pero algunos campos parecen estar destinados a un entorno de habla hispana (ej. el nombre del paquete "escuela").
    *   `DEBIAN/postinst`: Contiene comentarios en español.
    *   `usr/bin/escuela-domain-joiner`: La interfaz gráfica y los mensajes de error están íntegramente en portugués.
    *   `usr/share/applications/escuela-domain-joiner.desktop`: Etiquetas en portugués.
*   **Marcadores de Posición (Placeholders):**
    *   En `DEBIAN/control`, el campo `Maintainer` tiene el valor `Tu Nombre <admin@escuela.local>`, que debe ser actualizado con datos reales.

## 2. Errores Lógicos y de Configuración (Post-Instalación)
*   **Configuración de PAM (mkhomedir):** Un error común al unir equipos a un dominio es que los usuarios del dominio no pueden iniciar sesión porque su directorio personal no se crea automáticamente.
    *   *Sugerencia:* El script `postinst` debería ejecutar `pam-auth-update --enable mkhomedir` o asegurar que la dependencia `libpam-modules` esté configurada.
*   **Uso de `pkexec`:**
    *   La aplicación ejecuta `pkexec realm join ...`. Si el usuario no tiene privilegios de sudo o cancela el diálogo de PolicyKit, la aplicación maneja el error, pero podría ser más informativa sobre *por qué* falló (por ejemplo, distinguir entre "contraseña incorrecta" y "usuario sin permisos").
*   **Reinicio Forzado:** El script ofrece reiniciar con `pkexec reboot`. En algunos entornos, esto podría fallar si PolicyKit no está configurado para permitir reinicios sin contraseña desde una sesión de usuario.

## 3. Interfaz de Usuario (UI/UX)
*   **Dimensiones Fijas:** El uso de `root.geometry("450x650")` puede causar problemas de visualización en pantallas con resoluciones bajas o escalas de DPI altas. Es preferible dejar que la ventana se ajuste al contenido o usar dimensiones relativas.
*   **Créditos Estáticos:** La información del autor está "hardcodeada" en el código fuente. Para un paquete de distribución masiva, esto suele ir en un archivo de documentación aparte o ser más genérico.

## 4. Dependencias
*   Aunque `realmd`, `sssd`, y `adcli` están listados, se recomienda verificar si `samba-common-bin` es necesario para el descubrimiento de ciertos dominios antiguos o configuraciones específicas de NetBIOS, lo cual no está en la lista de `Depends`.

## 5. Seguridad
*   **Manejo de Contraseñas:** El script pasa la contraseña a través de un pipe (`stdin`). Aunque es más seguro que pasarla como argumento de línea de comandos (donde sería visible en `ps`), hay que asegurarse de que no se guarde en ningún log de depuración si se expande la funcionalidad de `--verbose`.
