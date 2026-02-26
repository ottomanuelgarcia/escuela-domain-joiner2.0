"""
Generación de configuración SSSD (System Security Services Daemon)
"""

import os
from .logger import logger


class SSSDConfigurator:
    """Manages SSSD configuration for AD integration"""

    def __init__(self, domain):
        self.domain = domain
        self.config_path = '/etc/sssd/sssd.conf'

    def generate_config(self, realm, ad_servers=None):
        """Genera configuración completa SSSD
        
        Args:
            realm: nombre del realm (ej: ESCUELA.LOCAL)
            ad_servers: lista de IPs/nombres de DC (opcional, usa discovery)
        
        Returns:
            str: contenido del sssd.conf
        """
        
        # Determinar servidores
        if ad_servers:
            ad_address = ', '.join(ad_servers)
        else:
            ad_address = 'None'  # Usar discovery automático
        
        config = f"""[sssd]
services = nss, pam, ssh, sudo
domains = {self.domain}

[domain/{self.domain}]
id_provider = ad
auth_provider = ad
chpass_provider = ad
access_provider = ad

realm = {realm}
krb5_realm = {realm}

ad_server = {ad_address}
ad_backup_server = None
ad_domain = {self.domain}

# Home directory templates
override_homedir = /home/%{{domain}}/%{{name}}
default_shell = /bin/bash

# Session management
session_provider = ad
subdomain_homedir = /home/%{{domain}}/%{{name}}

# Caching
cache_credentials = true
cache_credentials_minimal_pwd_length = 1
entry_cache_timeout = 5400
referral_member_rule = (member:1.2.840.113556.1.4.1941:=%%\(dn\))

# Performance
eno_groups_members = True
ignore_group_members = False

[nss]
filter_groups = root, wheel
filter_users = root
enum_cache_timeout = 120

[pam]
offline_credentials_expiration = 0
offline_failed_login_attempts = 0
offline_failed_login_delay = 0

[ssh]
# Enable SSH with SSSD

[sudo]
# Enable SUDO with SSSD
"""
        logger.info(f"Configuración SSSD generada para dominio {self.domain}")
        return config

    def apply_config(self, config_content):
        """Aplica la configuración usando pkexec
        
        Args:
            config_content: contenido del config a aplicar
        
        Returns:
            bool: éxito
        """
        import subprocess
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
                f.write(config_content)
                temp_path = f.name
            
            # Usar pkexec para copiar y establecer permisos
            subprocess.run(['pkexec', 'cp', temp_path, self.config_path], check=True, timeout=10)
            subprocess.run(['pkexec', 'chmod', '600', self.config_path], check=True, timeout=10)
            subprocess.run(['pkexec', 'chown', 'root:root', self.config_path], check=True, timeout=10)
            
            # Reiniciar SSSD
            subprocess.run(['pkexec', 'systemctl', 'restart', 'sssd'], check=True, timeout=30)
            
            logger.info(f"Configuración SSSD aplicada y servicio reiniciado")
            return True
        except Exception as e:
            logger.error(f"Error aplicando configuración SSSD: {e}")
            return False
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
