"""
Módulo para respaldar y restaurar configuraciones antes/después de unir al dominio
"""
import os
import shutil
import tarfile
import subprocess
from datetime import datetime
from .logger import logger

BACKUP_DIR = "/var/lib/escuela-domain-joiner/backups"

FILES_TO_BACKUP = [
    "/etc/sssd/sssd.conf",
    "/etc/samba/smb.conf",
    "/etc/krb5.conf",
    "/etc/lightdm/lightdm.conf",
    "/etc/nsswitch.conf",
    "/etc/pam.d/common-auth",
    "/etc/pam.d/common-session",
    "/etc/hosts",
]


def _ensure_backup_dir():
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)


def create_pre_join_backup():
    """Guarda archivos de configuración en un tar comprimido con timestamp."""
    _ensure_backup_dir()
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    path = os.path.join(BACKUP_DIR, f"prejoin_{ts}.tar.gz")
    logger.info(f"Creando backup previo a unión: {path}")
    with tarfile.open(path, "w:gz") as tar:
        for f in FILES_TO_BACKUP:
            if os.path.exists(f):
                tar.add(f)
    return path


def restore_original_config(backup_file):
    """Restaura los archivos desde un backup creado por create_pre_join_backup."""
    logger.info(f"Restaurando configuración desde {backup_file}")
    if not os.path.exists(backup_file):
        raise FileNotFoundError(backup_file)
    with tarfile.open(backup_file, "r:gz") as tar:
        tar.extractall(path="/")
    logger.info("Restauración completada")


def find_latest_backup():
    """Devuelve la ruta del backup prejoin más reciente o None."""
    if not os.path.isdir(BACKUP_DIR):
        return None
    backs = [f for f in os.listdir(BACKUP_DIR) if f.startswith('prejoin_') and f.endswith('.tar.gz')]
    if not backs:
        return None
    backs.sort(key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x)), reverse=True)
    return os.path.join(BACKUP_DIR, backs[0])


def save_template(domain):
    """Guarda la configuración actual como plantilla identificada por dominio y timestamp."""
    _ensure_backup_dir()
    templates_dir = os.path.join(BACKUP_DIR, 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"template_{domain}_{ts}.tar.gz"
    path = os.path.join(templates_dir, filename)
    logger.info(f"Guardando plantilla de configuración: {path}")
    with tarfile.open(path, "w:gz") as tar:
        for f in FILES_TO_BACKUP:
            if os.path.exists(f):
                tar.add(f)
    return path


def generate_error_report(domain=None, extra=None):
    """Genera un reporte simple con estado del sistema y logs relevantes."""
    reports_dir = os.path.join(BACKUP_DIR, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    report_file = os.path.join(reports_dir, f"error_report_{ts}.txt")
    logger.info(f"Generando reporte de error: {report_file}")
    try:
        with open(report_file, 'w') as rpt:
            rpt.write(f"Error report - {ts}\n")
            if domain:
                rpt.write(f"Domain: {domain}\n")
            if extra:
                rpt.write(f"Extra: {extra}\n")
            rpt.write("\n=== Service status ===\n")
            for svc in ['sssd', 'realmd']:
                try:
                    res = subprocess.run(['systemctl', 'status', svc, '--no-pager', '--lines=10'], capture_output=True, text=True, timeout=5)
                    rpt.write(f"--- {svc} ---\n")
                    rpt.write(res.stdout or res.stderr)
                except Exception as e:
                    rpt.write(f"Could not capture status for {svc}: {e}\n")
            rpt.write("\n=== End report ===\n")
    except Exception:
        logger.exception("No se pudo escribir el reporte de error")
    return report_file


def leave_domain(domain):
    """Ejecuta realm leave si el dominio sigue unido."""
    try:
        subprocess.run(['pkexec', 'realm', 'leave', domain], check=True, timeout=30)
        logger.info(f"Salió del dominio {domain} durante rollback")
    except Exception as e:
        logger.error(f"Error al ejecutar realm leave: {e}")


def verify_system_integrity():
    """Chequeo sencillo de que servicios claves están en marcha."""
    results = {}
    for service in ['sssd', 'realmd']:
        try:
            res = subprocess.run(['systemctl', 'is-active', service], capture_output=True, text=True, timeout=5)
            results[service] = (res.returncode == 0)
        except Exception:
            results[service] = False
    return results
