"""
Configuración PAM para autenticación de dominio y montaje automático de shares
"""

import os
import subprocess
from .logger import logger


class PAMConfigurator:
    """Configura PAM para AD y montaje de shares vía pam_mount"""

    def __init__(self):
        self.pam_mount_conf = '/etc/security/pam_mount.conf.xml'
        self.common_session = '/etc/pam.d/common-session'

    def enable_pam_mount(self):
        """Habilita pam_mount en common-session"""
        logger.info("Verificando configuración de pam_mount")
        
        try:
            with open(self.common_session, 'r') as f:
                content = f.read()
            
            if 'pam_mount.so' not in content:
                # Agregar línea pam_mount antes de pam_unix.so
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if 'pam_unix.so' in line and 'optional' not in line:
                        new_lines.append('session optional        pam_mount.so')
                    new_lines.append(line)
                
                new_content = '\n'.join(new_lines)
                self._write_pam_file(self.common_session, new_content)
                logger.info("pam_mount habilitado en common-session")
                return True
        except Exception as e:
            logger.error(f"Error configurando PAM: {e}")
            return False

    def configure_pam_auth(self):
        """Configura PAM para autenticación AD (common-auth)"""
        common_auth = '/etc/pam.d/common-auth'
        logger.info("Verificando configuración de autenticación PAM")
        
        try:
            with open(common_auth, 'r') as f:
                content = f.read()
            
            if 'pam_sss.so' not in content:
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if 'pam_permit.so' in line:
                        new_lines.append('auth    sufficient      pam_sss.so use_first_pass')
                
                new_content = '\n'.join(new_lines)
                self._write_pam_file(common_auth, new_content)
                logger.info("Autenticación SSSD habilitada en common-auth")
                return True
        except Exception as e:
            logger.error(f"Error configurando PAM auth: {e}")
            return False

    def generate_pam_mount_config(self, shares_xml):
        """Guarda configuración pam_mount
        
        Args:
            shares_xml: contenido XML generado por NetworkMapper
        """
        logger.info(f"Escribiendo configuración pam_mount")
        self._write_pam_file(self.pam_mount_conf, shares_xml)

    def _write_pam_file(self, filepath, content):
        """Escribe archivo PAM usando pkexec"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            subprocess.run(['pkexec', 'cp', temp_path, filepath], check=True, timeout=10)
            if filepath.endswith('.xml'):
                subprocess.run(['pkexec', 'chmod', '644', filepath], check=True)
            else:
                subprocess.run(['pkexec', 'chmod', '644', filepath], check=True)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
