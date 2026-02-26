"""
Excepciones personalizadas para Escuela Domain Joiner
"""


class DomainJoinerError(Exception):
    """Excepción base para errores del joinador de dominios"""
    pass


class DiscoveryError(DomainJoinerError):
    """Error durante autodeteción de dominios"""
    pass


class ConnectivityError(DiscoveryError):
    """Error verificando conectividad a dominio"""
    pass


class AuthenticationError(DomainJoinerError):
    """Error de autenticación"""
    pass


class ConfigurationError(DomainJoinerError):
    """Error en configuración del sistema"""
    pass


class BackupError(DomainJoinerError):
    """Error en backup/restore"""
    pass


class RollbackError(DomainJoinerError):
    """Error durante rollback"""
    pass


class SSSDError(ConfigurationError):
    """Error en configuración SSSD"""
    pass


class KerberosError(ConfigurationError):
    """Error en configuración Kerberos"""
    pass


class PAMError(ConfigurationError):
    """Error en configuración PAM"""
    pass


class SystemIntegrityError(DomainJoinerError):
    """Error verificando integridad del sistema"""
    pass
