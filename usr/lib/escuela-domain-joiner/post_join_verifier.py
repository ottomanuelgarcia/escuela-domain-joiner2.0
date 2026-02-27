"""
Verificación post-unión a dominio y coordinación de componentes de red
"""

import subprocess
import time
import os
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
try:
    from .sssd_config import SSSDConfigurator
    from .kerberos_config import KerberosConfigurator
    from .pam_config import PAMConfigurator
    from .network_mapper import NetworkMapper
except Exception:
    # fallback imports when executed as a standalone module (e.g. during tests)
    import importlib.util, os
    base = os.path.dirname(__file__)
    def _load(name, fname):
        path = os.path.join(base, fname)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    SSSDConfigurator = _load('sssd_config', 'sssd_config.py').SSSDConfigurator
    KerberosConfigurator = _load('kerberos_config', 'kerberos_config.py').KerberosConfigurator
    PAMConfigurator = _load('pam_config', 'pam_config.py').PAMConfigurator
    NetworkMapper = _load('network_mapper', 'network_mapper.py').NetworkMapper


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
        """Aplica configuraciones post-unión (wrapper)

        La lógica real se encuentra en :meth:`configure_post_join_full`.
        """
        return self.configure_post_join_full(home_mode, network_shares)
    
    def configure_post_join_full(self, home_mode='local', network_shares=None):
        """Implementation with home-mode, SSSD, pam_mount, and systemd mounts.

        This method encapsulates all the heavy lifting needed after a
        successful domain join. It is kept separate from the public wrapper
        to allow tests to call the implementation directly and to keep the
        public API simple.
        """
        logger.info(f"Configurando post-unión: home={home_mode}")
        try:
            try:
                from .session_manager import HomeDirectoryManager
            except Exception:
                import importlib.util
                base = os.path.dirname(__file__)
                spec = importlib.util.spec_from_file_location('session_manager', os.path.join(base, 'session_manager.py'))
                sm = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sm)
                HomeDirectoryManager = sm.HomeDirectoryManager
            hdm = HomeDirectoryManager(self.domain)
            if home_mode == 'local':
                hdm.configure_local()
            elif home_mode == 'remoto':
                hdm.configure_remoto(server='servidor.escuela.local', share_path='/homes')
            elif home_mode == 'hibrido':
                hdm.configure_hibrido()
    
            homedir_template = {
                'local': '/home/%{domain}/%{name}',
                'remoto': '%h',
                'hibrido': '/home/%{domain}/%{name}'
            }.get(home_mode, '/home/%{domain}/%{name}')
            sssd_snip = hdm.apply_sssd_override(homedir_template)
            cfg = self.sssd.generate_config(self.realm)
            if sssd_snip:
                cfg += "\n" + sssd_snip
            self.sssd.apply_config(cfg)

            if not self.pam.enable_pam_mount():
                logger.warning("PAM mount not enabled")

            if network_shares:
                mapper = NetworkMapper()
                if isinstance(network_shares, list):
                    mapper.map_shares_for_groups(network_shares)
                else:
                    mapper.shares = network_shares
                pam_xml = mapper.generate_pam_mount_xml()
                self.pam.generate_pam_mount_config(pam_xml)

                mounts = mapper.generate_systemd_mounts()
                for name, content in mounts.items():
                    dest = os.path.join('/etc/systemd/system', name)
                    try:
                        with open(dest + '.tmp', 'w') as f:
                            f.write(content)
                        subprocess.run(['pkexec', 'mv', dest + '.tmp', dest], check=True)
                    except Exception as e:
                        logger.warning(f"No se pudo escribir unidad {name}: {e}")

            subprocess.run(['pkexec', 'systemctl', 'restart', 'sssd'], timeout=30)
            time.sleep(2)

            logger.info("Configuración post-unión completada")
            return True
        except Exception as e:
            logger.error(f"Error en configuración post-unión: {e}")
            return False
    
