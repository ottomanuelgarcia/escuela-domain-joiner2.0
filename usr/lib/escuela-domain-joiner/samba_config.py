"""
Configuración Samba/Winbind para integración AD opcional
"""

import subprocess
import os
from .logger import logger


class SambaConfigurator:
    """Configura Samba/Winbind para integración con AD (alternativa a SSSD)"""

    def __init__(self, domain):
        self.domain = domain
        self.smb_conf = '/etc/samba/smb.conf'
        self.domain_short = domain.split('.')[0].upper()

    def generate_config(self, realm, ad_servers=None):
        """Genera configuración smb.conf para AD
        
        Args:
            realm: REALM.LOCAL (ej: ESCUELA.LOCAL)
            ad_servers: lista de servidores AD para winbind
        
        Returns:
            str: contenido de smb.conf
        """
        
        ads_server = ', '.join(ad_servers) if ad_servers else self.domain
        
        config = f"""[global]
    workgroup = {self.domain_short}
    realm = {realm}
    security = ads
    password server = {ads_server}
    
    # Winbind
    idmap config * : backend = tdb
    idmap config * : range = 2000-2999
    idmap config {self.domain_short} : backend = rid
    idmap config {self.domain_short} : range = 1000-1999
    
    # Integración SSSD+Samba
    username map = /etc/samba/user.map
    template shell = /bin/bash
    template homedir = /home/%D/%U
    
    # NSS
    winbind use default domain = yes
    winbind offline logon = no
    
    # Logging
    log file = /var/log/samba/%m.log
    max log size = 5000
    log level = 2
    
    # Performance
    socket options = TCP_NODELAY IPTOS_LOWDELAY SO_RCVBUF=131072 SO_SNDBUF=131072
    getwd cache = yes
    """
        logger.info(f"Configuración Samba generada para {realm}")
        return config

    def apply_config(self, config_content):
        """Aplica configuración (requiere Samba instalado)
        
        Args:
            config_content: contenido smb.conf
        
        Returns:
            bool: éxito
        """
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(config_content)
                temp_path = f.name
            
            # Validar sintaxis
            result = subprocess.run(
                ['pkexec', 'testparm', '-s', temp_path],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"Samba config invalída: {result.stderr.decode()}")
                return False
            
            # Aplicar
            subprocess.run(['pkexec', 'cp', temp_path, self.smb_conf], check=True, timeout=10)
            subprocess.run(['pkexec', 'chmod', '644', self.smb_conf], check=True, timeout=10)
            
            # Reiniciar
            subprocess.run(['pkexec', 'systemctl', 'restart', 'smbd'], timeout=30)
            subprocess.run(['pkexec', 'systemctl', 'restart', 'nmbd'], timeout=30)
            
            logger.info("Configuración Samba aplicada")
            return True
        except Exception as e:
            logger.error(f"Error aplicando Samba: {e}")
            return False
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def join_domain(self, username, password, ads_admin=None):
        """Une el sistema al dominio usando Samba
        
        Args:
            username: usuario administrativo
            password: contraseña
            ads_admin: formato alternativo (dominio\usuario)
        
        Returns:
            bool: éxito
        """
        logger.info(f"Uniendo dominio con Samba ({username})...")
        
        try:
            # Usar expect o echo para pasar contraseña
            # NOTA: En producción usar mecanismos más seguros
            cmd = [
                'pkexec', 'net', 'ads', 'join',
                '-U', username,
                '-S', self.domain,
                '-w', self.domain_short
            ]
            
            result = subprocess.run(
                cmd,
                input=password,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Dominio unido con Samba")
                return True
            else:
                logger.error(f"Error uniendo dominio: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error en samba join: {e}")
            return False
