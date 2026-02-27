"""
Configuración Kerberos para autenticación SSO en dominio Active Directory
"""

import subprocess
try:
    from .logger import logger
except Exception:
    import importlib.util, os
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


class KerberosConfigurator:
    """Configuración automática de krb5.conf para AD"""

    def __init__(self):
        self.krb5_conf = '/etc/krb5.conf'

    def generate_config(self, realm, kdc_servers=None, domain=None):
        """Genera configuración krb5.conf para Active Directory
        
        Args:
            realm: REALM.LOCAL en mayúsculas (ej: ESCUELA.LOCAL)
            kdc_servers: lista de servidores KDC o None para autodetección
            domain: dominio DNS (ej: escuela.local)
        
        Returns:
            str: contenido de krb5.conf
        """
        
        if domain is None:
            domain = realm.lower()
        
        # KDC servers fallback
        if kdc_servers:
            kdc_list = '\n                '.join([f'kdc = {kdc}:88' for kdc in kdc_servers])
        else:
            # Usar SRV records discovery automáticamente
            kdc_list = 'kdc = None  # Auto-discovery via SRV records'
        
        config = f"""[libdefaults]
    default_realm = {realm}
    dns_lookup_realm = true
    dns_lookup_kdc = true
    ticket_lifetime = 24h
    renew_lifetime = 7d
    clock_skew = 300
    forwardable = true
    proxiable = false
    default_tgs_enctypes = aes256-cts-hmac-sha1-96 aes128-cts-hmac-sha1-96 rc4-hmac
    default_tkt_enctypes = aes256-cts-hmac-sha1-96 aes128-cts-hmac-sha1-96 rc4-hmac
    permitted_enctypes = aes256-cts-hmac-sha1-96 aes128-cts-hmac-sha1-96 rc4-hmac

[realms]
    {realm} = {{
        {kdc_list}
        admin_server = {domain}
        kpasswd_server = {domain}:464
        default_domain = {domain}
    }}

[domain_realm]
    .{domain} = {realm}
    {domain} = {realm}
    localhost = {realm}
    localhost.localdomain = {realm}

[logging]
    default = FILE:/var/log/krb5.log
    kdc = FILE:/var/log/krb5kdc.log
    admin_server = FILE:/var/log/kadmind.log

[capaths]
    {realm} = {{
    }}
"""
        logger.info(f"Configuración Kerberos generada para realm {realm}")
        return config

    def apply_config(self, config_content):
        """Aplica la configuración mediante pkexec
        
        Args:
            config_content: contenido del archivo de configuración
        
        Returns:
            bool: éxito
        """
        import tempfile
        import os
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as f:
                f.write(config_content)
                temp_path = f.name
            
            subprocess.run(['pkexec', 'cp', temp_path, self.krb5_conf], check=True, timeout=10)
            subprocess.run(['pkexec', 'chmod', '644', self.krb5_conf], check=True, timeout=10)
            subprocess.run(['pkexec', 'chown', 'root:root', self.krb5_conf], check=True, timeout=10)
            
            logger.info("Configuración Kerberos aplicada")
            return True
        except Exception as e:
            logger.error(f"Error aplicando configuración Kerberos: {e}")
            return False
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
