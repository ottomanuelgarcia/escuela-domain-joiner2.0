#!/usr/bin/env python3
"""
Simula los caminos SÍ (éxito) y NO (rollback) sin requerir realmd ni interacción GUI.
Crea un backup dummy, crea el marcador `pending_verify`, llama a las funciones relevantes
y reporta los artefactos creados (plantilla y reporte).
"""
import os
import tarfile
import tempfile
import importlib.util
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SIM_ROOT = os.path.join(ROOT, 'tmp_sim')
BACKUP_DIR = os.path.join(SIM_ROOT, 'backups')
PENDING_FILE = os.path.join(SIM_ROOT, 'pending_verify')
os.makedirs(SIM_ROOT, exist_ok=True)

# Helper to import module from project
def load_module_from_path(name, path):
    # Load source and execute into a fresh module namespace. This allows
    # handling relative imports (e.g., 'from .logger import logger') by
    # injecting a simple logger during simulation.
    with open(path, 'r') as fh:
        src = fh.read()

    # Simple logger for simulation
    class _SimLogger:
        def info(self, *a, **k):
            print('[LOG][INFO]', *a)
        def warning(self, *a, **k):
            print('[LOG][WARN]', *a)
        def error(self, *a, **k):
            print('[LOG][ERR]', *a)
        def exception(self, *a, **k):
            print('[LOG][EXC]', *a)

    # Replace relative import line to avoid ImportError
    src = src.replace("from .logger import logger", "logger = _SimLogger()")

    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))
    mod.__dict__['_SimLogger'] = _SimLogger
    try:
        exec(compile(src, path, 'exec'), mod.__dict__)
    except Exception:
        raise
    return mod

# Ensure backup dir
os.makedirs(BACKUP_DIR, exist_ok=True)

# Create a dummy backup tar so find_latest_backup finds something
dummy_path = os.path.join(BACKUP_DIR, f"prejoin_dummy_{datetime.now().strftime('%Y%m%d%H%M%S')}.tar.gz")
with tarfile.open(dummy_path, 'w:gz') as tar:
    # create a small temp file to include
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.write(b"dummy config")
    tf.flush()
    tf.close()
    tar.add(tf.name, arcname='dummy.conf')
    os.unlink(tf.name)
print(f"Created dummy backup: {dummy_path}")

# Create pending_verify
os.makedirs(os.path.dirname(PENDING_FILE), exist_ok=True)
with open(PENDING_FILE, 'w') as f:
    f.write('domain=escuela.local\n')
    f.write(f"timestamp={datetime.now().strftime('%Y%m%d%H%M%S')}\n")
print(f"Created pending marker: {PENDING_FILE}")

# Load backup_restore
br_path = os.path.join(ROOT, 'usr', 'lib', 'escuela-domain-joiner', 'backup_restore.py')
backup_mod = load_module_from_path('backup_restore', br_path)
# Override BACKUP_DIR inside module for simulation
try:
    backup_mod.BACKUP_DIR = BACKUP_DIR
except Exception:
    pass

# Simulate SÍ path: save_template and remove marker
print('\n--- SIMULACIÓN: Camino SÍ (éxito) ---')
try:
    tpl = backup_mod.save_template('escuela.local')
    print(f"Template guardada en: {tpl}")
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)
        print('Pending marker eliminado.')
    else:
        print('Pending marker no existía al remover.')
except Exception as e:
    print('Error durante simulación SÍ:', e)

# Recreate pending for NO path
with open(PENDING_FILE, 'w') as f:
    f.write('domain=escuela.local\n')
    f.write(f"timestamp={datetime.now().strftime('%Y%m%d%H%M%S')}\n")

# Load edj-verify-domain and call perform_rollback
edj_path = os.path.join(ROOT, 'usr', 'sbin', 'edj-verify-domain')
edj_mod = load_module_from_path('edj_verify_domain', edj_path)
# Override paths in edj module to point to local simulation dir
try:
    edj_mod.BACKUPS_DIR = BACKUP_DIR
    edj_mod.PENDING_FILE = PENDING_FILE
except Exception:
    pass

print('\n--- SIMULACIÓN: Camino NO (rollback) ---')
try:
    # Patch subprocess.run in both modules to avoid sudo prompts during simulation
    class _FakeResult:
        def __init__(self):
            self.returncode = 0
            self.stdout = ''
            self.stderr = ''

    def fake_run(cmd, *a, **kw):
        print('[SIM] subprocess.run:', cmd)
        return _FakeResult()

    try:
        backup_mod.subprocess.run = fake_run
    except Exception:
        pass
    try:
        edj_mod.subprocess.run = fake_run
    except Exception:
        pass

    ok = edj_mod.perform_rollback(domain='escuela.local')
    print(f'perform_rollback returned: {ok}')
except Exception as e:
    print('Error durante perform_rollback:', e)

# Check reports
reports_dir = os.path.join(BACKUP_DIR, 'reports')
if os.path.isdir(reports_dir):
    reports = sorted(os.listdir(reports_dir))
    print('\nReports found:')
    for r in reports:
        print(' -', os.path.join(reports_dir, r))
else:
    print('\nNo reports directory found.')

# Check templates
templates_dir = os.path.join(BACKUP_DIR, 'templates')
if os.path.isdir(templates_dir):
    templates = sorted(os.listdir(templates_dir))
    print('\nTemplates found:')
    for t in templates:
        print(' -', os.path.join(templates_dir, t))
else:
    print('\nNo templates directory found.')

print('\nSimulación completada.')
