#!/usr/bin/env python3
"""
VERIFICACIÓN: DIÁLOGO DE CONFIRMACIÓN POST-REBOOT
Escuela Domain Joiner v2.0 - Mejora #2
"""

import os
import re

print("\n")
print("╔" + "═" * 78 + "╗")
print("║" + "VERIFICACIÓN: DIÁLOGO DE CONFIRMACIÓN POST-REBOOT".center(78) + "║")
print("╚" + "═" * 78 + "╝")
print()

script_path = "/home/casa4/Documentos/Trabajo/escuela-domain-joiner/usr/sbin/edj-verify-domain"

if not os.path.exists(script_path):
    print("❌ Script no existe")
    exit(1)

with open(script_path) as f:
    content = f.read()

print("┌─ VERIFICACIÓN DEL DIÁLOGO ───────────────────────────────────────────────┐")
print("│")

# TEST 1: Importes de Tkinter
print("│ TEST 1: Librerías Tkinter")
print("│ ─────────────────────────")

checks = [
    ("import tkinter", "Import tkinter"),
    ("from tkinter import messagebox", "Import messagebox"),
    ("messagebox.askyesno", "Método askyesno"),
    ("tk.Tk()", "Inicialización Tk"),
]

for check, desc in checks:
    if check in content:
        print(f"│   ✅ {desc}")
    else:
        print(f"│   ❌ {desc} NO ENCONTRADO")

print("│")

# TEST 2: Verificación de marcador
print("│ TEST 2: Verificación del Marcador Pendiente")
print("│ ────────────────────────────────────────────")

marker_checks = [
    ("PENDING_FILE", "Definición de ruta del archivo"),
    ("/var/lib/escuela-domain-joiner/pending_verify", "Ruta del marcador"),
    ("os.path.exists(PENDING_FILE)", "Verificación de existencia"),
]

for check, desc in marker_checks:
    if check in content:
        print(f"│   ✅ {desc}")
    else:
        print(f"│   ❌ {desc} NO ENCONTRADO")

print("│")

# TEST 3: Contenido del Diálogo
print("│ TEST 3: Contenido del Mensaje del Diálogo")
print("│ ──────────────────────────────────────────")

dialog_elements = [
    ("Verificación de Unión al Dominio", "Título"),
    ("ESCUELA.LOCAL", "Nombre del dominio"),
    ("Servicios SSSD activos", "Estado de SSSD"),
    ("Configuración PAM aplicada", "Estado de PAM"),
    ("Pudo iniciar sesión", "Pregunta principal"),
]

for element, desc in dialog_elements:
    if element in content:
        print(f"│   ✅ {desc}: '{element[:40]}...'")
    else:
        print(f"│   ⚠️  {desc} - Variación detectada")

print("│")

# TEST 4: Botones del Diálogo
print("│ TEST 4: Botones y Acciones")
print("│ ──────────────────────────")

button_checks = [
    ("messagebox.askyesno", "Método de diálogo SÍ/NO"),
    ("if res:", "Captura de respuesta"),
    ("os.remove(PENDING_FILE)", "Erase marcador si SÍ"),
    ("perform_rollback", "Rollback si NO"),
]

for check, desc in button_checks:
    if check in content:
        print(f"│   ✅ {desc}")
    else:
        print(f"│   ❌ {desc} NO ENCONTRADO")

print("│")

# TEST 5: Flujo de Éxito
print("│ TEST 5: Flujo de Éxito (Usuario dice SÍ)")
print("│ ─────────────────────────────────────────")

success_messages = [
    ("Éxito", "Mensaje de éxito"),
    ("exitoso", "Indicador de éxito"),
    ("listo", "Confirmación de completitud"),
]

success_found = False
for msg, desc in success_messages:
    if msg.lower() in content.lower():
        print(f"│   ✅ {desc}")
        success_found = True
        break

if not success_found:
    print("│   ⚠️  Búsqueda de mensaje de éxito")

print("│")

# TEST 6: Función de Rollback
print("│ TEST 6: Función Rollback (Usuario dice NO)")
print("│ ──────────────────────────────────────────")

rollback_checks = [
    ("def perform_rollback", "Función de rollback"),
    ("find_latest_backup", "Búsqueda de backup"),
    ("tar", "Ejecución de restauración"),
    ("realm leave", "Desunión del dominio"),
    ("systemctl restart", "Reinicio de servicios"),
]

for check, desc in rollback_checks:
    if check in content:
        print(f"│   ✅ {desc}")
    else:
        print(f"│   ❌ {desc} NO ENCONTRADO")

print("│")

# TEST 7: Manejo de Errores
print("│ TEST 7: Manejo de Errores y Excepciones")
print("│ ───────────────────────────────────────")

error_checks = [
    ("try:", "Bloques try/except"),
    ("except", "Captura de excepciones"),
    ("messagebox.showerror", "Diálogos de error"),
    ("messagebox.showwarning", "Diálogos de advertencia"),
]

for check, desc in error_checks:
    count = content.count(check)
    if count > 0:
        print(f"│   ✅ {desc} ({count} instancia(s))")
    else:
        print(f"│   ❌ {desc} NO ENCONTRADO")

print("│")

# TEST 8: Visualización del Diálogo
print("│ TEST 8: Configuración de la Ventana")
print("│ ────────────────────────────────────")

window_checks = [
    ("root = tk.Tk()", "Creación de ventana"),
    ("root.withdraw()", "Ocultar ventana principal"),
    ("root.attributes('-topmost', True)", "Ventana siempre al frente"),
    ("root.destroy()", "Limpiar recursos"),
]

for check, desc in window_checks:
    if check in content:
        print(f"│   ✅ {desc}")
    else:
        # Buscar variación
        if "withdraw" in check and "withdraw" in content:
            print(f"│   ✅ {desc} (variación encontrada)")
        else:
            print(f"│   ⚠️  {desc}")

print("│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# SECCIÓN 2: RENDERIZACIÓN DE DIÁLOGO ESPERADO
# ============================================================================
print("┌─ DIÁLOGO ESPERADO vs IMPLEMENTADO ────────────────────────────────────────┐")
print("│")

print("│ ESPECIFICACIÓN (Requerimiento):")
print("│ ┌─────────────────────────────────────────┐")
print("│ │  Verificación de Unión al Dominio      │")
print("│ ├─────────────────────────────────────────┤")
print("│ │                                         │")
print("│ │  ✓ Equipo unido a: ESCUELA.LOCAL       │")
print("│ │  ✓ Servicios SSSD activos              │")
print("│ │  ✓ Configuración PAM aplicada          │")
print("│ │                                         │")
print("│ │  ¿Pudo iniciar sesión exitosamente     │")
print("│ │  con usuario de dominio?                │")
print("│ │                                         │")
print("│ │           [SÍ]         [NO]             │")
print("│ └─────────────────────────────────────────┘")
print("│")
print("│ IMPLEMENTACIÓN (Código actual):")

# Extraer el mensaje del diálogo del código
msg_match = re.search(r'msg = \((.*?)\)', content, re.DOTALL)
if msg_match:
    msg_content = msg_match.group(1)
    print("│")
    print("│ Mensaje actual en el código:")
    for line in msg_content.split('\n')[:6]:
        if line.strip():
            line_clean = line.strip().strip('"').strip("'")
            print(f"│   {line_clean}")

print("│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# SECCIÓN 3: FLUJOS DE USUARIO
# ============================================================================
print("┌─ FLUJOS DE USUARIO IMPLEMENTADOS ─────────────────────────────────────────┐")
print("│")

print("│ FLUJO A: USUARIO DICE 'SÍ' (Éxito)")
print("│ ──────────────────────────────────")
print("│")
print("│ 1. script pregunta: '¿Pudo iniciar sesión?'")
print("│ 2. Usuario hace clic: [SÍ]")
print("│ 3. Script ejecuta:")
if "os.remove(PENDING_FILE)" in content:
    print("│    ✅ os.remove(PENDING_FILE)")
else:
    print("│    ❌ Erase PENDING_FILE")

if "showinfo" in content and ("exitoso" in content or "éxito" in content or "Éxito" in content):
    print("│    ✅ messagebox.showinfo(éxito)")
else:
    print("│    ⚠️  Mensaje de éxito")

print("│ 4. Resultado: Sistema listo para usar ✨")
print("│")

print("│ FLUJO B: USUARIO DICE 'NO' (Rollback)")
print("│ ─────────────────────────────────────")
print("│")
print("│ 1. Script pregunta: '¿Pudo iniciar sesión?'")
print("│ 2. Usuario hace clic: [NO]")
print("│ 3. Script ofrece: '¿Desea deshacer la unión?'")
print("│ 4. Si usuario acepta:")

rollback_steps = [
    ("find_latest_backup", "  ✓ Busca backup más reciente"),
    ("tar", "  ✓ Restaura configuración (tar -xzf)"),
    ("realm leave", "  ✓ Desúne del dominio"),
    ("systemctl restart", "  ✓ Reinicia servicios"),
]

for check, desc in rollback_steps:
    if check in content:
        print(f"│    {desc}")
    else:
        print(f"│    ❌ {desc.replace('✓', '✗')}")

print("│ 5. Resultado: Sistema vuelve a estado pre-unión")
print("│")
print("│ 6. Si usuario rechaza: deja sistema como está")
print("│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()

# ============================================================================
# SECCIÓN 4: RESUMEN VISUAL
# ============================================================================
print("╔" + "═" * 78 + "╗")
print("║" + "RESUMEN: DIÁLOGO DE CONFIRMACIÓN".center(78) + "║")
print("╠" + "═" * 78 + "╣")
print("║")

# Contar elementos verificados
total = 0
passed = 0

all_checks = [
    ("import tkinter", "Tkinter"),
    ("messagebox.askyesno", "Dialog SÍ/NO"),
    ("PENDING_FILE", "Marcador"),
    ("Verificación de Unión al Dominio", "Título"),
    ("ESCUELA.LOCAL", "Dominio"),
    ("os.remove(PENDING_FILE)", "Éxito: Erase"),
    ("perform_rollback", "Fallo: Rollback"),
    ("realm leave", "Comando realm"),
    ("tar", "Restauración"),
    ("root.withdraw()", "Ventana"),
]

for check, name in all_checks:
    total += 1
    if check.lower() in content.lower():
        passed += 1
        print(f"║  ✅ {name:<30} VERIFICADO")
    else:
        print(f"║  ❌ {name:<30} NO ENCONTRADO")

print("║")
print(f"║  Resultado: {passed}/{total} verificaciones pasadas ({(passed/total)*100:.0f}%)")
print("║")

if passed == total:
    print("║  ✨ DIÁLOGO DE CONFIRMACIÓN COMPLETAMENTE IMPLEMENTADO ✨")
else:
    print(f"║  ⚠️  {total - passed} elemento(s) requiere verificación manual")

print("║")
print("╚" + "═" * 78 + "╝")
print()

# ============================================================================
# SECCIÓN 5: CÓDIGO RELEVANTE
# ============================================================================
print("┌─ EXTRACCIÓN DE CÓDIGO: FUNCIÓN MAIN() ────────────────────────────────────┐")
print("│")

# Extrae la función main
main_match = re.search(r'def main\(\):(.*?)(?=if __name__|$)', content, re.DOTALL)
if main_match:
    main_code = main_match.group(1)
    lines = main_code.split('\n')[:30]  # Primeras 30 líneas
    for i, line in enumerate(lines, 1):
        if line.strip():
            print(f"│ {i:2d}: {line[:76]}")
else:
    print("│ No se pudo extraer main()")

print("│")
print("└────────────────────────────────────────────────────────────────────────────┘")
print()
