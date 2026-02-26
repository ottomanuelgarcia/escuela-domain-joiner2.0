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
            logger.info("Intentando descubrimiento DNS SRV")
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
            logger.warning(f"Fallo en DNS SRV: {e}")

        # TODO: añadir mDNS, NetBIOS y escaneo de puertos más adelante
        # por ahora devolvemos los encontrados por DNS
        # Eliminar duplicados
        seen = set()
        unique = []
        for d in domains:
            if d['nombre'] not in seen:
                unique.append(d)
                seen.add(d['nombre'])
        self.discovered_domains = unique
        return unique

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
