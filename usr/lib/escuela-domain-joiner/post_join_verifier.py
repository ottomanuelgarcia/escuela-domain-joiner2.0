"""
Verificación post-unión a dominio y coordinación de componentes de red
"""

import subprocess
import time
from .logger import logger
from .sssd_config import SSSDConfigurator
from .kerberos_config import KerberosConfigurator
from .pam_config import PAMConfigurator
from .network_mapper import NetworkMapper


class PostJoinVerifier:
    """Verifica y finaliza la integración del dominio después de la unión"""

    def __init__(self, domain, realm):
        self.domain = domain
        self.realm = realm
        self.sssd = SSSDConfigurator(domain)
        self.krb5 = KerberosConfigurator()
        self.pam = PAMConfigurator()

    def verify_domain_join(self):
        """Verifica que la unión al dominio fue exitosa"""
        logger.info("Verificando unión al dominio...")
        
        checks = [
            self._check_realm_status(),
            self._check_sssd_status(),
            self._check_krb5_conf(),
            self._check_user_lookup(),
        ]
        
        success = all(checks)
        logger.info(f"Verificación de unión: {'OK' if success else 'FALLOS'}")
        return success

    def _check_realm_status(self):
        """Verifica que realm reconoce el dominio"""
        try:
            output = subprocess.run(
                ['pkexec', 'realm', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if self.domain in output.stdout or self.realm in output.stdout:
                logger.info("Realm status: OK")
                return True
        except Exception as e:
            logger.error(f"Error verificando realm: {e}")
        return False

    def _check_sssd_status(self):
        """Verifica que SSSD esté activo"""
        try:
            result = subprocess.run(
                ['pkexec', 'systemctl', 'is-active', 'sssd'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("SSSD status: active")
                return True
        except Exception as e:
            logger.error(f"Error verificando SSSD: {e}")
        return False

    def _check_krb5_conf(self):
        """Verifica que krb5.conf existe y contiene el realm"""
        try:
            with open('/etc/krb5.conf', 'r') as f:
                content = f.read()
                if self.realm in content:
                    logger.info("Kerberos config: OK")
                    return True
        except Exception as e:
            logger.error(f"Error verificando krb5.conf: {e}")
        return False

    def _check_user_lookup(self):
        """Intenta resolver un usuario del dominio"""
        try:
            result = subprocess.run(
                ['pkexec', 'id', 'root@' + self.domain],
                capture_output=True,
                timeout=10
            )
            logger.info("Usuario lookup: sistema respondiendo")
            return True
        except subprocess.TimeoutExpired:
            logger.error("Usuario lookup: timeout")
            return False
        except Exception as e:
            logger.error(f"Error en lookup: {e}")
            return False

    def configure_post_join(self, home_mode='local', network_shares=None):
        """Aplica configuraciones post-unión"""
        logger.info(f"Configurando post-unión: home={home_mode}")
        
        try:
            if not self.pam.enable_pam_mount():
                logger.warning("PAM mount not enabled")
            
            if network_shares:
                mapper = NetworkMapper()
                pam_xml = mapper.generate_pam_mount_xml()
                self.pam.generate_pam_mount_config(pam_xml)
            
            subprocess.run(['pkexec', 'systemctl', 'restart', 'sssd'], timeout=30)
            time.sleep(2)
            
            logger.info("Configuración post-unión completada")
            return True
        except Exception as e:
            logger.error(f"Error en configuración post-unión: {e}")
            return False