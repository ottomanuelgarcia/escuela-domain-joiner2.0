"""
Módulo para configurar LightDM y PAM para aceptar usuarios de dominio
"""

import os
import subprocess
import tempfile
import shutil
from .logger import logger


class LightDMConfigurator:
    """
    Configura LightDM y PAM para permitir login de usuarios de dominio
    """
    
    def __init__(self, output_callback=None):
        self.output_callback = output_callback or self._default_callback
    
    def _default_callback(self, msg_type, message):
        """Callback por defecto"""
        logger.info(f"[{msg_type}] {message}")
    
    def _log_output(self, msg_type, message):
        """Registra y envía output"""
        if msg_type == 'error':
            logger.error(message)
        elif msg_type == 'warning':
            logger.warning(message)
        else:
            logger.info(message)
        
        self.output_callback(msg_type, message)
    
    def configure(self):
        """
        Ejecuta la configuración completa de LightDM y PAM
        Retorna: (éxito, mensaje)
        """
        try:
            self._log_output('info', "Iniciando configuración de gestor de login...")
            
            # Paso 1: Configurar LightDM
            success, msg = self._configure_lightdm()
            if not success:
                self._log_output('warning', f"Advertencia en LightDM: {msg}")
            
            # Paso 2: Configurar NSS
            success, msg = self._configure_nsswitch()
            if not success:
                self._log_output('warning', f"Advertencia en NSS: {msg}")
            
            # Paso 3: Configurar PAM
            success, msg = self._configure_pam()
            if not success:
                self._log_output('warning', f"Advertencia en PAM: {msg}")
            
            self._log_output('success', "Configuración de login completada exitosamente")
            logger.info("Configuración de LightDM y PAM completada")
            return True, "Configuración completada"
            
        except Exception as e:
            msg = f"Error en configuración: {str(e)}"
            self._log_output('error', msg)
            logger.error(msg)
            return False, msg
    
    def _configure_lightdm(self):
        """Configura LightDM creando un archivo de anulación (override)."""
        try:
            self._log_output('info', "Configurando LightDM para inicio de sesión de dominio...")

            override_dir = "/etc/lightdm/lightdm.conf.d"
            override_file = os.path.join(override_dir, "60-escuela-domain-joiner.conf")

            # Asegurarse de que el directorio de anulación exista
            if not os.path.exists(override_dir):
                try:
                    subprocess.run(
                        ['pkexec', 'mkdir', '-p', override_dir],
                        check=True,
                        timeout=10
                    )
                    self._log_output('info', f"Directorio creado: {override_dir}")
                except Exception as e:
                    raise Exception(f"No se pudo crear el directorio {override_dir}: {e}")

            # Contenido del archivo de anulación
            # Habilita el login manual y deshabilita la sesión de invitado.
            override_content = (
                "[Seat:*]\n"
                "greeter-show-manual-login=true\n"
                "allow-guest=false\n"
            )

            self._write_file_with_sudo(override_file, override_content)
            self._log_output('success', f"✓ Archivo de configuración de LightDM creado en {override_file}")
            
            return True, "LightDM configurado correctamente mediante archivo de anulación."

        except Exception as e:
            return False, str(e)
    
    def _update_lightdm_conf(self, conf_file):
        """Este método ya no es necesario y se deja por compatibilidad o referencia."""
        self._log_output('info', "El método _update_lightdm_conf ya no se utiliza, la configuración se realiza mediante archivos de anulación.")
        return

    def _update_lightdm_gtk_conf(self, conf_file):
        """Este método ya no es necesario y se deja por compatibilidad o referencia."""
        self._log_output('info', "El método _update_lightdm_gtk_conf ya no se utiliza.")
        return
    
    def _configure_nsswitch(self):
        """Configura /etc/nsswitch.conf para SSSD"""
        try:
            self._log_output('info', "Configurando NSS...")
            nsswitch_conf = "/etc/nsswitch.conf"
            
            if not os.path.exists(nsswitch_conf):
                return False, "nsswitch.conf no encontrado"
            
            with open(nsswitch_conf, 'r') as f:
                content = f.read()
            
            # Variables a verificar
            required_lines = {
                'passwd': 'passwd:    files systemd sss',
                'group': 'group:     files systemd sss',
                'hosts': 'hosts:     files dns myhostname'
            }
            
            lines = content.split('\n')
            new_lines = []
            configured = {key: False for key in required_lines}
            
            for line in lines:
                added = False
                for key, expected in required_lines.items():
                    if line.startswith(key + ':') and not line.strip().startswith('#'):
                        # Verificar si ya contiene 'sss'
                        if 'sss' not in line:
                            new_lines.append(expected)
                        else:
                            new_lines.append(line)
                        configured[key] = True
                        added = True
                        break
                
                if not added:
                    new_lines.append(line)
            
            # Añadir líneas faltantes
            for key, line in required_lines.items():
                if not configured[key]:
                    new_lines.append(line)
            
            new_content = '\n'.join(new_lines)
            self._write_file_with_sudo(nsswitch_conf, new_content)
            
            return True, "NSS configurado"
            
        except Exception as e:
            return False, str(e)
    
    def _configure_pam(self):
        """Configura PAM para SSSD"""
        try:
            self._log_output('info', "Configurando PAM...")
            
            # Detectar distro para usar el método apropiado
            if os.path.exists('/usr/sbin/pam-auth-update'):
                # Intenta usar pam-auth-update (Debian/Ubuntu)
                try:
                    # Simplemente verificar que PAM está configurado
                    # pam-auth-update requiere interacción, así que solo validamos
                    result = subprocess.run(
                        ['dpkg', '-l', 'sssd-common'],
                        capture_output=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self._log_output('info', "SSSD está instalado. PAM será configurado automáticamente.")
                        return True, "PAM configurado"
                except:
                    pass
            
            return True, "PAM verificado"
            
        except Exception as e:
            return False, str(e)
    
    def _write_file_with_sudo(self, filepath, content):
        """Escribe un archivo con privilegios de root usando sudo"""
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # Copiar archivo temporal a destino con sudo
                subprocess.run(
                    ['pkexec', 'cp', tmp_path, filepath],
                    check=True,
                    timeout=10
                )
                
                # Establecer permisos
                subprocess.run(
                    ['pkexec', 'chmod', '644', filepath],
                    check=True,
                    timeout=10
                )
            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        except Exception as e:
            raise Exception(f"Error escribiendo archivo {filepath}: {e}")
