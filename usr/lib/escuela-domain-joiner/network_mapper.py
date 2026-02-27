"""
Mapeo automático de unidades de red según membresía de grupos Active Directory
"""

import os

try:
    from .logger import logger
except Exception:
    import importlib.util
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


class NetworkMapper:
    """Mapea shares CIFS/NFS basado en membresía de grupos AD"""

    # Configuración de shares por grupo
    GROUPS_CONFIG = {
        'Alumnos': [
            {'nombre': 'Recursos', 'ruta': '//servidor/recursos_compartidos', 'punto': '~/Red/Recursos', 'permisos': 'ro'},
            {'nombre': 'Trabajos', 'ruta': '//servidor/trabajos_alumnos', 'punto': '~/Red/Mis_Trabajos', 'permisos': 'rw'},
            {'nombre': 'Software', 'ruta': '//servidor/software', 'punto': '~/Red/Software', 'permisos': 'ro'},
        ],
        'Profesores': [
            {'nombre': 'Recursos', 'ruta': '//servidor/recursos_compartidos', 'punto': '~/Red/Recursos', 'permisos': 'rw'},
            {'nombre': 'Didactica', 'ruta': '//servidor/material_didactico', 'punto': '~/Red/Didactica', 'permisos': 'rw'},
            {'nombre': 'Privado', 'ruta': '//servidor/profesores', 'punto': '~/Red/Privado', 'permisos': 'rw'},
            {'nombre': 'Trabajos_Alumnos', 'ruta': '//servidor/trabajos_alumnos', 'punto': '~/Red/Trabajos_Alumnos', 'permisos': 'ro'},
        ],
        'Administracion': [
            {'nombre': 'Todos', 'ruta': '//servidor/recursos_compartidos', 'punto': '~/Red/Recursos', 'permisos': 'rw'},
            {'nombre': 'Admin', 'ruta': '//servidor/administracion', 'punto': '~/Red/Admin', 'permisos': 'rw'},
            {'nombre': 'Contabilidad', 'ruta': '//servidor/contabilidad', 'punto': '~/Red/Contabilidad', 'permisos': 'rw'},
        ]
    }

    def __init__(self):
        self.shares = []

    def map_shares_for_groups(self, groups):
        """Retorna lista de shares para una lista de grupos
        
        Args:
            groups: lista de nombres de grupos (ej: ['Alumnos', 'Profesores'])
        
        Returns:
            list: configuración de shares a montar
        """
        shares = []
        for group in groups:
            if group in self.GROUPS_CONFIG:
                shares.extend(self.GROUPS_CONFIG[group])
        
        # Eliminar duplicados por nombre de unidad
        seen = {}
        unique_shares = []
        for share in shares:
            if share['nombre'] not in seen:
                seen[share['nombre']] = True
                unique_shares.append(share)
        
        self.shares = unique_shares
        logger.info(f"Mapeo de shares para grupos {groups}: {len(unique_shares)} unidades")
        return unique_shares

    def generate_pam_mount_xml(self, server='servidor.escuela.local'):
        """Genera configuración XML para pam_mount
        
        Args:
            server: nombre del servidor
        
        Returns:
            str: contenido XML
        """
        xml = """<?xml version="1.0" encoding="UTF-8" ?>
<pam_mount>
  <debug enable="0" />
  <mntoptions allow="*" />
  <mntoptions require="nosuid,nodev" />
  <logout wait="0" hup="no" term="no" kill="no" />
\n"""
        
        for share in self.shares:
            # Limpiar ruta
            ruta = share['ruta'].replace('//', '').replace('//servidor/', '')
            opciones = 'sec=krb5i,cruid=%(USERUID),iocharset=utf8,vers=3.0'
            if share['permisos'] == 'ro':
                opciones += ',ro'
            
            xml += f'''  <volume user="*" fstype="cifs" server="{server}" path="{ruta}" 
           mountpoint="{share['punto']}" options="{opciones}" />
'''
        
        xml += "</pam_mount>"
        return xml

    def generate_systemd_mounts(self, server='servidor.escuela.local'):
        """Genera unidades systemd .mount para auto-montaje
        
        Returns:
            dict: {nombre_unidad: contenido}
        """
        import hashlib
        mounts = {}
        for share in self.shares:
            ruta = share['ruta'].lstrip('/')
            what = f"//{server}/{ruta}"
            # Use %h placeholder so systemd can expand to the user's home at runtime
            where = share['punto'].replace('~', '%h')

            # Generate stable, safe unit name using hash of the target path
            name_hash = hashlib.sha1(f"{what}:{where}".encode('utf-8')).hexdigest()[:12]
            unit_name = f"edj-{name_hash}.mount"

            content = f"""[Unit]
Description=Montaje de {share['nombre']} ({what})
After=network-online.target
Wants=network-online.target

[Mount]
What={what}
Where={where}
Type=cifs
Options=sec=krb5i,cruid=%U,iocharset=utf8,_netdev

[Install]
WantedBy=multi-user.target
"""
            mounts[unit_name] = content

        return mounts
