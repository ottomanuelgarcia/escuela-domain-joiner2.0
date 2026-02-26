"""
Módulo para validación y verificación de dominio
"""

import subprocess
import socket
import re
from .logger import logger


def validate_domain_format(domain):
    """
    Valida el formato básico del dominio
    Debe contener al menos un punto
    """
    if not domain or not isinstance(domain, str):
        return False, "Dominio inválido"
    
    domain = domain.strip()
    
    # Validar que tenga al menos un punto
    if '.' not in domain:
        return False, "El dominio debe contener al menos un punto (ej: escuela.edu)"
    
    # Validar caracteres válidos
    pattern = r'^[a-zA-Z0-9.-]+$'
    if not re.match(pattern, domain):
        return False, "El dominio contiene caracteres inválidos"
    
    return True, domain


def validate_ou_format(ou):
    """
    Valida el formato básico de la Unidad Organizativa LDAP
    """
    if not ou or ou.strip() == "":
        return True, None  # OU es opcional
    
    ou = ou.strip()
    
    # Validar que contenga estructura LDAP mínima
    if not ("OU=" in ou.upper() and "DC=" in ou.upper()):
        return False, "Formato OU inválido. Use: OU=...,DC=...,DC=..."
    
    return True, ou


def resolve_domain_dns(domain):
    """
    Intenta resolver el dominio usando DNS
    Retorna: (éxito, mensaje, ip)
    """
    try:
        logger.info(f"Resolviendo DNS para: {domain}")
        ip = socket.getaddrinfo(domain, None)[0][4][0]
        logger.info(f"Dominio resuelto: {domain} -> {ip}")
        return True, f"Dominio resolvible: {ip}", ip
    except socket.gaierror as e:
        msg = f"Error al resolver DNS para {domain}: {str(e)}"
        logger.warning(msg)
        return False, msg, None
    except Exception as e:
        msg = f"Error inesperado al resolver DNS: {str(e)}"
        logger.error(msg)
        return False, msg, None


def discover_realm(domain):
    """
    Ejecuta 'realm discover' para obtener información del dominio
    Retorna: (éxito, mensaje, salida_completa)
    """
    try:
        logger.info(f"Descubriendo dominio: {domain}")
        result = subprocess.run(
            ['realm', 'discover', domain],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Realm discover exitoso para: {domain}")
            return True, "Dominio Kerberos descoberto exitosamente", result.stdout
        else:
            msg = result.stderr if result.stderr else result.stdout
            logger.warning(f"Realm discover falló: {msg}")
            return False, msg, result.stdout + result.stderr
            
    except subprocess.TimeoutExpired:
        msg = "Timeout al intentar descubrir el dominio (30s)"
        logger.error(msg)
        return False, msg, ""
    except FileNotFoundError:
        msg = "Comando 'realm' no encontrado. Instala 'realmd'"
        logger.error(msg)
        return False, msg, ""
    except Exception as e:
        msg = f"Error al descubrir dominio: {str(e)}"
        logger.error(msg)
        return False, msg, ""


def check_current_domain():
    """
    Verifica si el equipo ya está unido a un dominio
    Retorna: (está_unido, nombre_dominio)
    """
    try:
        logger.info("Verificando estado del dominio...")
        result = subprocess.run(
            ['realm', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Parsear la salida para obtener el nombre del dominio
            lines = result.stdout.strip().split('\n')
            if lines:
                domain_name = lines[0].strip()
                logger.info(f"Equipo ya unido a dominio: {domain_name}")
                return True, domain_name
        
        logger.info("Equipo no unido a ningún dominio")
        return False, None
        
    except subprocess.TimeoutExpired:
        logger.warning("Timeout al verificar dominio")
        return False, None
    except FileNotFoundError:
        logger.error("Comando 'realm' no encontrado")
        return False, None
    except Exception as e:
        logger.error(f"Error al verificar dominio: {str(e)}")
        return False, None
