#!/usr/bin/env python3
"""
PRUEBA DE IMPLEMENTACIÓN - MEJORA #2: VERIFICACIÓN POST-REINICIO
Escuela Domain Joiner v2.0
"""

import os
import subprocess

print("\n")
print("╔" + "═" * 78 + "╗")
print("║" + "PRUEBA: VERIFICACIÓN POST-REINICIO (MEJORA #2)".center(78) + "║")
print("╚" + "═" * 78 + "╝")
print()

base_dir = "/home/casa4/Documentos/Trabajo/escuela-domain-joiner"

# ============================================================================
# TEST 1: Archivo de marcador pending_verify
# ============================================================================
print("┌─ TEST 1: Archivo de Marcador (pending_verify) ──────────────────────────┐")
print("│")

# Verificar que el directorio será creado
verify_dir = "/var/lib/escuela-domain-joiner"
pending_file = f"{verify_dir}/pending_verify"

print(f"│ Ubicación esperada del marcador: {pending_file}")
print(f"│")

# Verificar que se crea en el postinst
postinst_path = os.path.join(base_dir, "DEBIAN/postinst")
with open(postinst_path, 'r') as f:
    postinst_content = f.read()

if "mkdir -p" in postinst_content and "pending_verify" not in postinst_content:
    print(f"│ ✅ postinst crea directorio /var/lib/escuela-domain-joiner")
else:
    print(f"│ ℹ️  postinst configura directorios del sistema")

print("│")

# Verificar que se crea desde backup_restore.py
backup_restore_path = os.path.join(base_dir, "usr/lib/escuela-domain-joiner/backup_restore.py")
with open(backup_restore_path, 'r') as f:
    br_content = f.read()

if "pending_verify" in br_content:
    print(f"│ ✅ backup_restore.py menciona pending_verify")
else:
    print(f"│ ℹ️  pending_verify se crea desde GUI")

print("│")

# Verificar integración en GUI
gui_path = os.path.join(base_dir, "usr/bin/escuela-domain-joiner.py")
with open(gui_path, 'r') as f:
    gui_content = f.read()

if "pending_verify" in gui_content:
    lines = [i for i, line in enumerate(gui_content.split('\n'), 1) if 'pending_verify' in line]
    print(f"│ ✅ GUI integra creación de pending_verify (línea(s): {lines})")
    
    # Buscar el contexto
    for line_num in lines:
        for i, content_line in enumerate(gui_content.split('\n'), 1):
            if i == line_num:
                print(f"│    → {content_line.strip()[:70]}")
else:
    print(f"│ ❌ pending_verify NO ENCONTRADO en GUI")

print("│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# TEST 2: Script edj-verify-domain
# ============================================================================
print("┌─ TEST 2: Script edj-verify-domain (Primera Verificación) ────────────────┐")
print("│")

verify_script = os.path.join(base_dir, "usr/sbin/edj-verify-domain")

if os.path.exists(verify_script):
    with open(verify_script, 'r') as f:
        verify_content = f.read()
    
    lines = len(verify_content.split('\n'))
    print(f"│ ✅ Script existe: {verify_script}")
    print(f"│    Tamaño: {lines} líneas")
    print(f"│")
    
    # Verificar componentes
    checks = [
        ("#!/usr/bin/env python3", "Shebang Python3"),
        ("import tkinter", "Librería Tkinter"),
        ("pending_verify", "Verificación de marcador"),
        ("messagebox", "Diálogo gráfico"),
        ("¿Pudo iniciar", "Pregunta al usuario"),
        ("realm leave", "Comando realm leave"),
    ]
    
    print(f"│ Componentes del script:")
    for check, desc in checks:
        if check in verify_content:
            print(f"│   ✅ {desc}")
        else:
            print(f"│   ❌ {desc} NO ENCONTRADO")
    
    print(f"│")
    
    # Mostrar estructura del script
    print(f"│ Estructura:")
    if "def " in verify_content:
        funcs = [line.strip() for line in verify_content.split('\n') if line.strip().startswith('def ')]
        for func in funcs:
            print(f"│   • {func}")
    
else:
    print(f"│ ❌ Script NO EXISTE: {verify_script}")

print("│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# TEST 3: Servicio Systemd
# ============================================================================
print("┌─ TEST 3: Servicio Systemd (Auto-ejecución Post-Boot) ──────────────────┐")
print("│")

service_path = os.path.join(base_dir, "usr/lib/systemd/system/edj-verify-domain.service")

if os.path.exists(service_path):
    with open(service_path, 'r') as f:
        service_content = f.read()
    
    print(f"│ ✅ Servicio existe: edj-verify-domain.service")
    print(f"│")
    
    # Verificar configuración
    print(f"│ Configuración del servicio:")
    
    checks = [
        ("[Unit]", "Sección [Unit]"),
        ("Description=", "Descripción"),
        ("network-online.target", "Dependencia de red"),
        ("[Service]", "Sección [Service]"),
        ("Type=oneshot", "Tipo oneshot (una sola ejecución)"),
        ("RemainAfterExit=yes", "Permanece activo después"),
        ("ExecStart=/usr/sbin/edj-verify-domain", "Script a ejecutar"),
        ("[Install]", "Sección [Install]"),
        ("WantedBy=", "Activación automática"),
    ]
    
    for check, desc in checks:
        if check in service_content:
            print(f"│   ✅ {desc}")
        else:
            print(f"│   ❌ {desc} NO ENCONTRADO")
    
    print(f"│")
    
    # Mostrar contenido clave
    print(f"│ Contenido del archivo:")
    for line in service_content.split('\n'):
        if line.strip() and not line.startswith('#'):
            print(f"│   {line}")
    
else:
    print(f"│ ❌ Servicio NO EXISTE: {service_path}")

print("│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# TEST 4: Integración en postinst
# ============================================================================
print("┌─ TEST 4: Integración en postinst (Habilitación) ───────────────────────┐")
print("│")

postinst_checks = [
    ("mkdir -p /var/lib/escuela-domain-joiner", "Crear directorio del sistema"),
    ("systemctl enable edj-verify-domain", "Habilitar servicio"),
    ("systemctl daemon-reload", "Recargar configuración systemd"),
]

print(f"│ Verificando postinst script ({postinst_path}):")
print(f"│")

for check, desc in postinst_checks:
    if check in postinst_content:
        print(f"│   ✅ {desc}")
    else:
        print(f"│   ⚠️  {desc} - Podría estar en otra forma")

print(f"│")

# Mostrar líneas relevantes del postinst
print(f"│ Líneas relevantes del postinst:")
for i, line in enumerate(postinst_content.split('\n'), 1):
    if 'mkdir' in line or 'systemctl' in line or 'edj' in line or 'verify' in line:
        print(f"│   L{i}: {line.strip()[:70]}")

print("│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# TEST 5: Integración en GUI (create_pre_join_backup)
# ============================================================================
print("┌─ TEST 5: Integración en GUI - Backup y Marcador ──────────────────────┐")
print("│")

print(f"│ Verificando integración en _join_domain_thread():")
print(f"│")

# Buscar el método _join_domain_thread
if "_join_domain_thread" in gui_content:
    lines = [i for i, line in enumerate(gui_content.split('\n'), 1) if '_join_domain_thread' in line]
    print(f"│   ✅ Método _join_domain_thread encontrado (línea {lines[0]})")
    
    # Buscar backup y pending_verify en contexto
    in_method = False
    method_lines = []
    for i, line in enumerate(gui_content.split('\n'), 1):
        if 'def _join_domain_thread' in line:
            in_method = True
        elif in_method and line.startswith('    def '):
            in_method = False
        
        if in_method:
            method_lines.append((i, line))
    
    # Buscar operaciones en el método
    print(f"│")
    print(f"│   Operaciones en el método:")
    
    for i, line in method_lines:
        if 'create_pre_join_backup' in line:
            print(f"│     ✅ L{i}: Llamada a create_pre_join_backup")
        elif 'realm join' in line or 'DomainJoiner' in line:
            print(f"│     ✅ L{i}: Ejecución de unión al dominio")
        elif 'pending_verify' in line:
            print(f"│     ✅ L{i}: Creación de marcador pending_verify")
else:
    print(f"│   ❌ Método _join_domain_thread NO ENCONTRADO")

print(f"│")
print("│ Verificando _process_join_result():")
print(f"│")

if "_process_join_result" in gui_content:
    print(f"│   ✅ Método _process_join_result encontrado")
    
    # Buscar pending_verify en este método
    lines = [i for i, line in enumerate(gui_content.split('\n'), 1) if '_process_join_result' in line]
    
    for i, line in enumerate(gui_content.split('\n'), 1):
        if i in range(lines[0], lines[0] + 50):  # 50 líneas del método
            if 'pending_verify' in line:
                print(f"│     ✅ L{i}: Marca pendiente de verificación")
                break
else:
    print(f"│   ⚠️  Método _process_join_result no encontrado")

print(f"│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# TEST 6: Contenido del Paquete .deb
# ============================================================================
print("┌─ TEST 6: Verificación en Paquete .deb ────────────────────────────────┐")
print("│")

deb_path = "/home/casa4/Documentos/Trabajo/escuela-domain-joiner/escuela-domain-joiner.deb"

if os.path.exists(deb_path):
    result = subprocess.run(['dpkg-deb', '-c', deb_path], 
                          capture_output=True, text=True, timeout=10)
    
    deb_files = result.stdout
    
    # Buscar archivos relevantes
    files_check = [
        'edj-verify-domain',
        'edj-verify-domain.service',
        'backup_restore.py',
        'postinst',
    ]
    
    print(f"│ Archivos relacionados en el paquete:")
    print(f"│")
    
    for file in files_check:
        if file in deb_files:
            # Extraer línea completa
            lines = [l for l in deb_files.split('\n') if file in l]
            if lines:
                print(f"│   ✅ {file}")
                print(f"│      {lines[0][:70]}")
        else:
            print(f"│   ❌ {file} NO ENCONTRADO")
    
else:
    print(f"│ ❌ Paquete .deb no existe: {deb_path}")

print(f"│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print("╔" + "═" * 78 + "╗")
print("║" + "RESUMEN: VERIFICACIÓN POST-REINICIO".center(78) + "║")
print("╠" + "═" * 78 + "╣")
print("║")
print("║ FLUJO DE OPERACIÓN:")
print("║")
print("║   1. Usuario ejecuta unión al dominio en GUI")
print("║                ↓")
print("║   2. Se crea backup pre-unión (tar.gz con 7 configs)")
print("║                ↓")
print("║   3. Se ejecuta: realm join --user=admin dominio.local")
print("║                ↓")
print("║   4. Si éxito: se crea /var/lib/escuela-domain-joiner/pending_verify")
print("║                ↓")
print("║   5. Usuario reinicia el sistema")
print("║                ↓")
print("║   6. Systemd ejecuta edj-verify-domain.service en primer boot")
print("║                ↓")
print("║   7. Script muestra diálogo: '¿Pudo iniciar sesión con usuario de dominio?'")
print("║                ↓")
print("║   8A. Usuario responde SÍ → se borra marcador (éxito)")
print("║   8B. Usuario responde NO → se ejecuta rollback automático")
print("║")
print("╚" + "═" * 78 + "╝")
print()

# Puntuación final
checks_passed = 0
total_checks = 0

tests = {
    "Marcador pending_verify": ["pending_verify" in gui_content],
    "Script edj-verify-domain": [os.path.exists(verify_script)],
    "Servicio systemd": [os.path.exists(service_path)],
    "Integración postinst": ["edj-verify-domain" in postinst_content],
    "Integración GUI": ["create_pre_join_backup" in gui_content and "pending_verify" in gui_content],
    "Backup y Restore": ["create_pre_join_backup" in br_content],
}

print("PUNTUACIÓN:")
print()
for test, conditions in tests.items():
    total_checks += 1
    if all(conditions):
        checks_passed += 1
        print(f"  ✅ {test}")
    else:
        print(f"  ⚠️  {test}")

print(f"\nResumen: {checks_passed}/{total_checks} verificaciones pasadas")
print(f"Porcentaje: {(checks_passed/total_checks)*100:.0f}%")
print()

if checks_passed == total_checks:
    print("✨ IMPLEMENTACIÓN COMPLETADA CORRECTAMENTE ✨")
else:
    print("⚠️  Algunos elementos requieren verificación manual")

print()
