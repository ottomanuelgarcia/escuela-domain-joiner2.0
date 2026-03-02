"""
Módulo de descubrimiento automático de dominios Active Directory
"""

import socket
import subprocess
import dns.resolver
import re
from .logger import logger


class DomainDiscovery:
    """Provee métodos para localizar dominios en la red"""

    def __init__(self, timeout=5):
        self.discovered_domains = []
        self.timeout = timeout

    def discover_all(self):
        """Ejecuta todos los métodos de descubrimiento y devuelve lista de dominios.

        Retorna
        -------
        list of dict
            Cada elemento contiene keys: nombre, controlador, metodo, confiable
        """
        domains = []
        
        # Prioridad 1: DNS SRV
        try:
            logger.info("Intentando descubrimiento por DNS SRV...")
            answers = dns.resolver.resolve("_ldap._tcp.dc._msdcs", "SRV", lifetime=self.timeout)
            for rdata in answers:
                target = str(rdata.target).rstrip('.')
                domain = target.split('.', 1)[1] if '.' in target else target
                domains.append({
                    'nombre': domain,
                    'controlador': target,
                    'metodo': 'dns_srv',
                    'confiable': True
                })
        except Exception as e:
            logger.warning(f"Fallo en descubrimiento por DNS SRV: {e}")

        # Prioridad 2: Realm Discover
        try:
            logger.info("Intentando descubrimiento por 'realm discover'...")
            result = subprocess.run(['realm', 'discover'], capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout:
                discovered_realms = self._parse_realm_discover_output(result.stdout)
                for realm in discovered_realms:
                    domains.append({
                        'nombre': realm['domain-name'],
                        'controlador': realm.get('server-software', 'desconocido'),
                        'metodo': 'realm_discover',
                        'confiable': True
                    })
        except FileNotFoundError:
            logger.warning("'realm' no está instalado. Saltando descubrimiento por realm.")
        except subprocess.TimeoutExpired:
            logger.warning("'realm discover' tardó demasiado en responder.")
        except Exception as e:
            logger.error(f"Error inesperado con 'realm discover': {e}")

        # Eliminar duplicados, dando prioridad a los métodos más confiables
        seen = set()
        unique = []
        for d in sorted(domains, key=lambda x: x['confiable'], reverse=True):
            if d['nombre'] not in seen:
                unique.append(d)
                seen.add(d['nombre'])
        
        self.discovered_domains = unique
        return unique

    def _parse_realm_discover_output(self, output):
        """Parsea la salida del comando 'realm discover'."""
        realms = []
        current_realm = {}
        for line in output.strip().split('\n'):
            line = line.strip()
            if not line:
                if current_realm:
                    realms.append(current_realm)
                    current_realm = {}
                continue
            
            if ':' in line:
                key, value = line.split(':', 1)
                current_realm[key.strip()] = value.strip()

        if current_realm:
            realms.append(current_realm)
            
        return realms

    def test_domain_connectivity(self, domain_name):
        """Verifica puertos clave del dominio.

        Retorna un dict con el estado booleano de cada puerto.
        """
        ports = {88: False, 389: False, 445: False, 464: False}
        for port in ports:
            try:
                with socket.create_connection((domain_name, port), timeout=3):
                    ports[port] = True
            except Exception:
                ports[port] = False
        return ports

    def get_ous_from_domain(self, domain_name):
        """Consulta OUs mediante ldap3 (requiere conectividad y credenciales).

        Por el momento devuelve lista vacía como stub.
        """
        # implementación futura
        logger.info(f"Solicitando OUs para dominio {domain_name} (no implementado)")
        return []
