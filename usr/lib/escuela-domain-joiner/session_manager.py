"""
Gestión de home directories con tres modalidades: Local, Remoto, Híbrido
"""

import os
import subprocess
try:
    from .logger import logger
except Exception:
    import importlib.util
    pkg_dir = os.path.dirname(__file__)
    logger_path = os.path.join(pkg_dir, 'logger.py')
    if os.path.exists(logger_path):
        spec = importlib.util.spec_from_file_location('edj_logger', logger_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        logger = getattr(mod, 'logger', None)
    else:
        import logging
        logging.basicConfig()
        logger = logging.getLogger('edj')


class HomeDirectoryManager:
    """Gestiona configuración de directorios home para usuarios de dominio"""

    MODES = ['local', 'remoto', 'hibrido']

    def __init__(self, domain_name, base_path='/home'):
        self.domain_name = domain_name
        self.base_path = base_path
        self.domain_short = domain_name.split('.')[0].upper()

    def configure_local(self):
        """Configura home local: /home/DOMINIO/usuario"""
        logger.info(f"Configurando home local en {self.base_path}/{self.domain_short}")
        home_dir = os.path.join(self.base_path, self.domain_short)
        try:
            os.makedirs(home_dir, mode=0o755, exist_ok=True)
            logger.info(f"Home local: {home_dir}")
            return True
        except Exception as e:
            logger.error(f"Error creando home local: {e}")
            return False

    def configure_remoto(self, server, share_path):
        """Configura home remoto montado vía CIFS/NFS
        
        Args:
            server: servidor.dominio.local
            share_path: /homes o /home_profiles
        """
        logger.info(f"Configurando home remoto en //{server}{share_path}")
        # Configuración mediante pam_mount en postinst
        return True

    def configure_hibrido(self, sync_tool='rsync'):
        """Configura home híbrido con sync local
        
        Args:
            sync_tool: rsync o unison
        """
        logger.info(f"Configurando home híbrido con {sync_tool}")
        config = {
            'sync_tool': sync_tool,
            'sync_on_login': True,
            'sync_on_logout': True,
            'cache_timeout': 300  # segundos
        }
        return config

    def apply_sssd_override(self, homedir_template):
        """Genera configuración SSSD para override de home
        
        Args:
            homedir_template: %d = dominio, %u = usuario
        """
        conf = f"""
[domain/{self.domain_name}]
override_homedir = {homedir_template}
fallback_homedir = {self.base_path}/%u
shell = /bin/bash
default_shell = /bin/bash
"""
        logger.info(f"Template SSSD homedir: {homedir_template}")
        return conf
