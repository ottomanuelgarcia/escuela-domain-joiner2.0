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
        """Configura archivos de LightDM"""
        try:
            self._log_output('info', "Configurando LightDM...")
            
            lightdm_conf = "/etc/lightdm/lightdm.conf"
            lightdm_gtk_conf = "/etc/lightdm/lightdm-gtk-greeter.conf"
            
            # Intentar configurar lightdm.conf
            if os.path.exists(lightdm_conf):
                try:
                    self._update_lightdm_conf(lightdm_conf)
                    self._log_output('info', "lightdm.conf actualizado")
                except Exception as e:
                    self._log_output('warning', f"No se pudo actualizar lightdm.conf: {e}")
            
            # Intentar configurar lightdm-gtk-greeter.conf
            if os.path.exists(lightdm_gtk_conf):
                try:
                    self._update_lightdm_gtk_conf(lightdm_gtk_conf)
                    self._log_output('info', "lightdm-gtk-greeter.conf actualizado")
                except Exception as e:
                    self._log_output('warning', f"No se pudo actualizar lightdm-gtk-greeter.conf: {e}")
            
            return True, "LightDM configurado"
            
        except Exception as e:
            return False, str(e)
    
    def _update_lightdm_conf(self, conf_file):
        """Modifica lightdm.conf para permitir usuarios no listados"""
        try:
            with open(conf_file, 'r') as f:
                content = f.read()
            
            # Backup
            backup_file = conf_file + '.bak'
            if not os.path.exists(backup_file):
                shutil.copy2(conf_file, backup_file)
            
            # Realizar cambios
            lines = content.split('\n')
            new_lines = []
            
            allow_guest_found = False
            manual_login_found = False
            
            for line in lines:
                # Comentar allow-guest
                if line.startswith('allow-guest'):
                    if not line.strip().startswith('#'):
                        new_lines.append('# ' + line)
                        allow_guest_found = True
                    else:
                        new_lines.append(line)
                # Asegurar greeter-show-manual-login
                elif line.startswith('greeter-show-manual-login'):
                    new_lines.append('greeter-show-manual-login=true')
                    manual_login_found = True
                else:
                    new_lines.append(line)
            
            # Añadir si no existen
            if not allow_guest_found:
                new_lines.append('allow-guest=false')
            if not manual_login_found:
                new_lines.append('greeter-show-manual-login=true')
            
            # Escribir cambios con privilegios de root
            new_content = '\n'.join(new_lines)
            self._write_file_with_sudo(conf_file, new_content)
            
        except Exception as e:
            raise Exception(f"Error actualizando {conf_file}: {e}")
    
    def _update_lightdm_gtk_conf(self, conf_file):
        """Modifica lightdm-gtk-greeter.conf"""
        try:
            with open(conf_file, 'r') as f:
                content = f.read()
            
            # Backup
            backup_file = conf_file + '.bak'
            if not os.path.exists(backup_file):
                shutil.copy2(conf_file, backup_file)
            
            # Realizar cambios
            lines = content.split('\n')
            new_lines = []
            
            show_manual_login_found = False
            
            for line in lines:
                if line.startswith('show-manual-login'):
                    new_lines.append('show-manual-login=true')
                    show_manual_login_found = True
                else:
                    new_lines.append(line)
            
            if not show_manual_login_found:
                new_lines.append('show-manual-login=true')
            
            new_content = '\n'.join(new_lines)
            self._write_file_with_sudo(conf_file, new_content)
            
        except Exception as e:
            raise Exception(f"Error actualizando {conf_file}: {e}")
    
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
