"""
Configuración PAM para autenticación de dominio y montaje automático de shares
"""

import os
import subprocess
import shutil
import tempfile
import re
try:
    from .logger import logger
except Exception:
    # Fallback when module is loaded as a script during tests: load logger.py by path
    import importlib.util
    pkg_dir = os.path.dirname(__file__)
    logger_path = os.path.join(pkg_dir, 'logger.py')
    if os.path.exists(logger_path):
        spec = importlib.util.spec_from_file_location('edj_logger', logger_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        logger = getattr(mod, 'logger', None)
    else:
        # Minimal logger fallback
        import logging
        logging.basicConfig()
        logger = logging.getLogger('edj')


class PAMConfigurator:
    """Configura PAM para AD y montaje de shares vía pam_mount"""

    def __init__(self, pam_mount_conf='/etc/security/pam_mount.conf.xml', common_session='/etc/pam.d/common-session'):
        self.pam_mount_conf = pam_mount_conf
        self.common_session = common_session

    def enable_pam_mount(self):
        """Habilita pam_mount en common-session"""
        logger.info("Verificando configuración de pam_mount")
        try:
            with open(self.common_session, 'r') as f:
                content = f.read()

            if 'pam_mount.so' in content:
                logger.info("pam_mount ya presente en common-session")
                return True

            # Insertar antes de la primera línea pam_unix.so que no sea optional, usando regex
            pattern = re.compile(r'^(.*pam_unix\.so.*)$', re.MULTILINE)
            match = pattern.search(content)
            if match:
                # Construir nueva línea
                insert_line = 'session optional        pam_mount.so'
                # Insertar antes de la línea encontrada
                start = match.start(1)
                # Encontrar inicio de la línea
                line_start = content.rfind('\n', 0, start) + 1
                new_content = content[:line_start] + insert_line + '\n' + content[line_start:]
            else:
                # No se encontró pam_unix.so, añadir al final
                new_content = content + '\n' + 'session optional        pam_mount.so\n'

            # Respaldar
            try:
                backup_path = self.common_session + '.edj.bak'
                shutil.copy2(self.common_session, backup_path)
                logger.info(f"Backup creado: {backup_path}")
            except Exception:
                logger.warning("No se pudo crear backup de common-session")

            if self._write_pam_file(self.common_session, new_content):
                logger.info("pam_mount habilitado en common-session")
                return True
            else:
                logger.error("Fallo al escribir common-session")
                return False
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
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Si el destino es escribible por el usuario actual, usar replace directo
            dest_dir = os.path.dirname(filepath) or '.'
            if (not os.path.exists(filepath) and os.access(dest_dir, os.W_OK)) or (os.path.exists(filepath) and os.access(filepath, os.W_OK)):
                try:
                    os.replace(temp_path, filepath)
                    os.chmod(filepath, 0o644)
                    logger.info(f"Archivo escrito directamente: {filepath}")
                    return True
                except Exception as e:
                    logger.warning(f"Escritura directa falló: {e}, intentando pkexec")

            # Fallback a pkexec para entornos protegidos
            subprocess.run(['pkexec', 'cp', temp_path, filepath], check=True, timeout=10)
            subprocess.run(['pkexec', 'chmod', '644', filepath], check=True)
            return True
        except Exception as e:
            logger.error(f"Error escribiendo archivo PAM: {e}")
            return False
        finally:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
