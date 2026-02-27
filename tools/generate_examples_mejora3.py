#!/usr/bin/env python3
"""
Genera ejemplos para Mejora #3 en /tmp/edj_examples
- sssd.conf ejemplo
- pam_mount.conf.xml generado
- unidades .mount generadas
"""
import os
import importlib.util
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(repo_root, 'usr', 'lib', 'escuela-domain-joiner')

# Helper to load module by filename
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

sssd_mod = load_module('sssd_config', os.path.join(lib_dir, 'sssd_config.py'))
net_mod = load_module('network_mapper', os.path.join(lib_dir, 'network_mapper.py'))
session_mod = load_module('session_manager', os.path.join(lib_dir, 'session_manager.py'))

outdir = '/tmp/edj_examples'
os.makedirs(outdir, exist_ok=True)

# Generate sssd.conf example
sssd_conf = sssd_mod.SSSDConfigurator('escuela.local').generate_config('ESCUELA.LOCAL', ad_servers=['dc1.escuela.local','dc2.escuela.local'])
with open(os.path.join(outdir, 'sssd.conf.example'), 'w') as f:
    f.write(sssd_conf)

# Generate network mapper outputs
mapper = net_mod.NetworkMapper()
shares = mapper.map_shares_for_groups(['Alumnos','Profesores'])

pam_xml = mapper.generate_pam_mount_xml(server='servidor.escuela.local')
with open(os.path.join(outdir, 'pam_mount.conf.xml.example'), 'w') as f:
    f.write(pam_xml)

mounts = mapper.generate_systemd_mounts(server='servidor.escuela.local')
mounts_dir = os.path.join(outdir, 'systemd_mounts')
os.makedirs(mounts_dir, exist_ok=True)
for name, content in mounts.items():
    with open(os.path.join(mounts_dir, name), 'w') as f:
        f.write(content)

print('Ejemplos generados en', outdir)
print('Shares mapeados:', [s['nombre'] for s in shares])
