#!/usr/bin/env python3
"""
Escuela Domain Joiner v2.0
Herramienta gráfica para untar equipos a dominio Active Directory
Autor: MSc. Otto Manuel Garcia Preval
"""

import sys
import os
import threading
import queue
from pathlib import Path

# Añadir la ruta de librerías
sys.path.insert(0, '/usr/lib/escuela-domain-joiner')

try:
    import tkinter as tk
    from tkinter import messagebox, ttk, scrolledtext
except ImportError:
    print("Error: El módulo 'tkinter' no está instalado.")
    print("Por favor, instálelo ejecutando: sudo apt install python3-tk")
    sys.exit(1)

from domain_checker import (
    validate_domain_format, 
    validate_ou_format,
    resolve_domain_dns,
    discover_realm,
    check_current_domain
)
from domain_discovery import DomainDiscovery
from domain_joiner import DomainJoiner
from domain_leaver import DomainLeaver
from lightdm_config import LightDMConfigurator
from backup_restore import create_pre_join_backup
from logger import logger


class DomainJoinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ingressar no Domínio da Escola - v2.0")
        self.root.geometry("700x850")
        self.root.minsize(600, 700)
        self.root.resizable(True, True)
        self.center_window()

        # Variables de estado
        self.current_domain = None
        self.is_joined = False
        self.process_queue = queue.Queue()
        
        # Style customization
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        # Header
        self._create_header()
        
        # Main Content Frame
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Canvas com scrollbar para soportar contenido largo
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mousewheel para scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sección de Estado
        self._create_status_section(scrollable_frame)

        # Sección de Información de Dominio
        self._create_domain_section(scrollable_frame)

        # Sección de Credenciales
        self._create_credentials_section(scrollable_frame)

        # Sección de Configuración Avanzada
        self._create_advanced_section(scrollable_frame)

        # Sección de Progreso
        self._create_progress_section(scrollable_frame)

        # Sección de Botones
        self._create_buttons_section(scrollable_frame)

        # Sección de Créditos
        self._create_credits_section(scrollable_frame)

        # Verificar estado inicial del dominio
        self._check_initial_state()

    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _create_header(self):
        """Crea el encabezado de la aplicación"""
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill="x")
        header_label = tk.Label(
            header_frame,
            text="Configuração de Domínio v2.0",
            bg="#2c3e50",
            fg="white",
            font=("Helvetica", 14, "bold")
        )
        header_label.pack(pady=15)

    def _create_status_section(self, parent):
        """Crea la sección de estado del dominio"""
        status_frame = tk.LabelFrame(parent, text="Estado del Dominio", padx=15, pady=10)
        status_frame.pack(fill="x", pady=(0, 15))

        self.status_icon_label = tk.Label(status_frame, font=("Arial", 16))
        self.status_icon_label.pack(side="left", padx=(0, 10))

        self.status_text_label = tk.Label(
            status_frame,
            text="Verificando estado...",
            fg="#2980b9",
            wraplength=500,
            justify="left"
        )
        self.status_text_label.pack(side="left", fill="both", expand=True)

    def _create_domain_section(self, parent):
        """Crea la sección de información de dominio"""
        domain_frame = tk.LabelFrame(parent, text="Información de Dominio", padx=15, pady=10)
        domain_frame.pack(fill="x", pady=(0, 15))

        # Dominio
        tk.Label(domain_frame, text="Nome do Domínio (ex. escisah.edu):", anchor="w").pack(fill="x")
        
        domain_input_frame = tk.Frame(domain_frame)
        domain_input_frame.pack(fill="x", pady=(0, 10))
        
        self.domain_entry = ttk.Entry(domain_input_frame)
        self.domain_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # botón buscar dominio
        self.discovery_button = ttk.Button(
            domain_input_frame,
            text="🔍 BUSCAR AHORA",
            width=18,
            command=self._search_domain
        )
        self.discovery_button.pack(side="left", padx=(0,5))

        self.test_connection_button = ttk.Button(
            domain_input_frame,
            text="Probar Conexión",
            command=self._test_connection,
            width=15
        )
        self.test_connection_button.pack(side="left")

        # Test result
        self.test_result_label = tk.Label(domain_frame, text="", fg="#27ae60", wraplength=450)
        self.test_result_label.pack(fill="x", pady=(0, 10))

        # dropdown de dominios detectados
        self.discovered_var = tk.StringVar()
        self.discovered_dropdown = ttk.Combobox(domain_frame, textvariable=self.discovered_var, state="readonly")
        self.discovered_dropdown.pack(fill="x", pady=(0,5))
        self.discovered_dropdown.bind("<<ComboboxSelected>>", self._on_domain_selected)

    def _create_credentials_section(self, parent):
        """Crea la sección de credenciales"""
        cred_frame = tk.LabelFrame(parent, text="Credenciales", padx=15, pady=10)
        cred_frame.pack(fill="x", pady=(0, 15))

        # Usuario
        tk.Label(cred_frame, text="Usuário Administrador:", anchor="w").pack(fill="x")
        self.user_entry = ttk.Entry(cred_frame)
        self.user_entry.insert(0, "Administrator")
        self.user_entry.pack(fill="x", pady=(0, 10))

        # Contraseña
        tk.Label(cred_frame, text="Senha:", anchor="w").pack(fill="x")
        
        pass_frame = tk.Frame(cred_frame)
        pass_frame.pack(fill="x", pady=(0, 5))
        
        self.password_entry = ttk.Entry(pass_frame, show="*")
        self.password_entry.pack(side="left", fill="x", expand=True)

        # Mostrar/Ocultar contraseña
        self.show_pass_var = tk.IntVar()
        self.show_pass_check = ttk.Checkbutton(
            cred_frame,
            text="Mostrar senha",
            variable=self.show_pass_var,
            command=self._toggle_password
        )
        self.show_pass_check.pack(anchor="w", pady=(0, 10))

    def _create_advanced_section(self, parent):
        """Crea la sección de configuración avanzada"""
        advanced_frame = tk.LabelFrame(parent, text="Configuración Avanzada", padx=15, pady=10)
        advanced_frame.pack(fill="x", pady=(0, 15))

        tk.Label(
            advanced_frame,
            text="Unidad Organizativa (Opcional):",
            anchor="w"
        ).pack(fill="x")
        
        tk.Label(
            advanced_frame,
            text="Ej: OU=Computadoras,DC=escuela,DC=local",
            fg="#7f8c8d",
            font=("Arial", 9)
        ).pack(fill="x", pady=(0, 5))
        
        self.ou_entry = ttk.Entry(advanced_frame)
        self.ou_entry.pack(fill="x", pady=(0, 10))

    def _create_progress_section(self, parent):
        """Crea la sección de progreso y log"""
        progress_frame = tk.LabelFrame(parent, text="Progreso y Registro", padx=15, pady=10)
        progress_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='indeterminate'
        )
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # Área de texto para logs
        self.log_text = scrolledtext.ScrolledText(
            progress_frame,
            height=10,
            width=60,
            bg="#ecf0f1",
            fg="#2c3e50",
            font=("Courier", 9)
        )
        self.log_text.pack(fill="both", expand=True, pady=(0, 10))

        # Tags para colores
        self.log_text.tag_config("info", foreground="#2980b9")
        self.log_text.tag_config("success", foreground="#27ae60", font=("Courier", 9, "bold"))
        self.log_text.tag_config("warning", foreground="#f39c12")
        self.log_text.tag_config("error", foreground="#e74c3c")

        # Botón para limpiar log
        clear_log_button = ttk.Button(
            progress_frame,
            text="Limpiar Registro",
            command=self._clear_log
        )
        clear_log_button.pack(anchor="e")

    def _create_buttons_section(self, parent):
        """Crea la sección de botones de acción"""
        button_frame = tk.Frame(parent)
        button_frame.pack(fill="x", pady=(0, 15))

        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self.root.destroy)
        self.cancel_button.pack(side="right", padx=5)

        self.leave_button = ttk.Button(
            button_frame,
            text="Sair do Dominio",
            command=self._leave_domain,
            state="disabled"
        )
        self.leave_button.pack(side="right", padx=5)

        self.join_button = ttk.Button(
            button_frame,
            text="Ingressar",
            command=self._join_domain_thread
        )
        self.join_button.pack(side="right", padx=5)

    def _create_credits_section(self, parent):
        """Crea la sección de créditos"""
        credits_frame = tk.LabelFrame(parent, text="Sobre o Autor", padx=10, pady=10)
        credits_frame.pack(fill="x", pady=(20, 0))
        
        credits_text = (
            "Este programa foi criado pelo MSc. Otto Manuel Garcia Preval.\n"
            "Versão 2.0 - Con mejoras de validación y gestión avanzada.\n"
            "Você pode contatá-lo:\n"
            "Telefone: 948199810\n"
            "E-mail: ottomanuelgarcia@gmail.com"
        )
        tk.Label(credits_frame, text=credits_text, justify="center", fg="#555").pack()

    def _toggle_password(self):
        """Alterna visibilidad de contraseña"""
        if self.show_pass_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def _log_message(self, msg_type, message):
        """Añade un mensaje al log"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n", msg_type)
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.root.update_idletasks()

    def _clear_log(self):
        """Limpia el log"""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _check_initial_state(self):
        """Verifica el estado inicial del dominio en background"""
        def check():
            is_joined, domain = check_current_domain()
            self.process_queue.put(('state', is_joined, domain))
        
        threading.Thread(target=check, daemon=True).start()
        self.root.after(500, self._process_state_queue)

    def _process_state_queue(self):
        """Procesa la cola de estado"""
        try:
            while True:
                item = self.process_queue.get_nowait()
                if item[0] == 'state':
                    _, is_joined, domain = item
                    self._update_domain_state(is_joined, domain)
        except queue.Empty:
            self.root.after(500, self._process_state_queue)

    def _update_domain_state(self, is_joined, domain):
        """Actualiza la UI según el estado del dominio"""
        self.is_joined = is_joined
        self.current_domain = domain

        if is_joined and domain:
            # Dominio ya configurado
            self.status_icon_label.config(text="✓", fg="#27ae60")
            self.status_text_label.config(
                text=f"Este equipo ya pertenece al dominio:\n{domain}",
                fg="#27ae60"
            )

            # Deshabilitar campos y botones de unión
            self.domain_entry.config(state="disabled")
            self.user_entry.config(state="disabled")
            self.password_entry.config(state="disabled")
            self.ou_entry.config(state="disabled")
            self.show_pass_check.config(state="disabled")
            self.test_connection_button.config(state="disabled")
            self.join_button.config(state="disabled")
            self.discovery_button.config(state="disabled")

            # Habilitar botón de desunión
            self.leave_button.config(state="normal")
            
            self._log_message('success', f"✓ Dominio detectado: {domain}")
        else:
            # No hay dominio configurado
            self.status_icon_label.config(text="✗", fg="#e74c3c")
            self.status_text_label.config(
                text="Este equipo no está unido a ningún dominio",
                fg="#e74c3c"
            )

            # Habilitar todos los campos
            self.domain_entry.config(state="normal")
            self.user_entry.config(state="normal")
            self.password_entry.config(state="normal")
            self.ou_entry.config(state="normal")
            self.show_pass_check.config(state="normal")
            self.test_connection_button.config(state="normal")
            self.join_button.config(state="normal")
            self.discovery_button.config(state="normal")

            # Deshabilitar botón de desunión
            self.leave_button.config(state="disabled")
            
            self._log_message('info', "Preparado para untar a un nuevo dominio")

    def _search_domain(self):
        """Busca dominios mediante varios métodos y llena el dropdown"""
        self.discovery_button.config(state="disabled")
        self.test_result_label.config(text="Buscando dominios en la red...", fg="#f39c12")
        self._log_message('info', "Iniciando descubrimiento de dominios")

        def search():
            dd = DomainDiscovery()
            results = dd.discover_all()
            self.process_queue.put(('discovery', results))

        threading.Thread(target=search, daemon=True).start()
        self.root.after(500, self._process_discovery)

    def _process_discovery(self):
        try:
            while True:
                item = self.process_queue.get_nowait()
                if item[0] == 'discovery':
                    _, results = item
                    self.discovery_button.config(state="normal")
                    if results:
                        names = [r['nombre'] for r in results]
                        self.discovered_dropdown['values'] = names
                        self.test_result_label.config(text=f"{len(names)} dominio(s) encontrado(s)", fg="#27ae60")
                    else:
                        self.test_result_label.config(text="No se detectó dominio automáticamente", fg="#e74c3c")
                    return
        except queue.Empty:
            self.root.after(500, self._process_discovery)

    def _on_domain_selected(self, event=None):
        sel = self.discovered_var.get()
        if sel:
            self.domain_entry.delete(0, 'end')
            self.domain_entry.insert(0, sel)

    def _test_connection(self):
        """Prueba conexión al dominio"""
        domain = self.domain_entry.get().strip()
        
        # Validar dominio
        valid, msg = validate_domain_format(domain)
        if not valid:
            self.test_result_label.config(text=f"❌ {msg}", fg="#e74c3c")
            self._log_message('error', f"Validación: {msg}")
            return

        self.test_connection_button.config(state="disabled")
        self.progress_bar.start()
        self.test_result_label.config(text="Probando conexión...", fg="#f39c12")

        def test():
            self._log_message('info', f"Resolviendo DNS para: {domain}")
            
            # Resolver DNS
            dns_ok, dns_msg, ip = resolve_domain_dns(domain)
            
            if not dns_ok:
                self.process_queue.put(('test_result', False, dns_msg))
                return

            self._log_message('success', f"✓ DNS resuelto: {ip}")
            self._log_message('info', "Descobriendo dominio Kerberos...")
            
            # Descubrir realm
            realm_ok, realm_msg, output = discover_realm(domain)
            
            if not realm_ok:
                self.process_queue.put(('test_result', False, realm_msg))
            else:
                self._log_message('success', "✓ Dominio descoberto exitosamente")
                self.process_queue.put(('test_result', True, f"Dominio accesible: {domain}"))

        threading.Thread(target=test, daemon=True).start()
        self.root.after(500, self._process_test_result)

    def _process_test_result(self):
        """Procesa el resultado de la prueba"""
        try:
            while True:
                item = self.process_queue.get_nowait()
                if item[0] == 'test_result':
                    _, success, message = item
                    self.progress_bar.stop()
                    self.test_connection_button.config(state="normal")
                    
                    if success:
                        self.test_result_label.config(
                            text=f"✓ {message}",
                            fg="#27ae60"
                        )
                    else:
                        self.test_result_label.config(
                            text=f"❌ {message}",
                            fg="#e74c3c"
                        )
                    return
        except queue.Empty:
            self.root.after(500, self._process_test_result)

    def _join_domain_thread(self):
        """Inicia la unión al dominio en thread separado"""
        domain = self.domain_entry.get().strip()
        user = self.user_entry.get().strip()
        password = self.password_entry.get().strip()
        ou = self.ou_entry.get().strip()

        # Validaciones
        if not domain or not user or not password:
            messagebox.showerror("Error", "Por favor, preencha dominio, usuário e senha.")
            return

        valid, msg = validate_domain_format(domain)
        if not valid:
            messagebox.showerror("Error", f"Dominio inválido: {msg}")
            return

        if ou:
            valid, msg = validate_ou_format(ou)
            if not valid:
                messagebox.showerror("Error", f"OU inválida: {msg}")
                return

        # crear backup previo a la unión
        try:
            backup_path = create_pre_join_backup()
            self._log_message('info', f"Backup creado: {backup_path}")
        except Exception as e:
            self._log_message('warning', f"No se pudo crear backup previo: {e}")

        self.join_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.domain_entry.config(state="disabled")
        self.user_entry.config(state="disabled")
        self.password_entry.config(state="disabled")
        self.ou_entry.config(state="disabled")
        self.test_connection_button.config(state="disabled")

        self.progress_bar.start()
        self._log_message('info', f"Iniciando unión a dominio: {domain}")

        def join():
            joiner = DomainJoiner(output_callback=self._log_message)
            success, msg = joiner.join(domain, user, password, ou)
            self.process_queue.put(('join_result', success, domain, msg))

        threading.Thread(target=join, daemon=True).start()
        self.root.after(500, self._process_join_result)

    def _process_join_result(self):
        """Procesa el resultado de la unión"""
        try:
            while True:
                item = self.process_queue.get_nowait()
                if item[0] == 'join_result':
                    _, success, domain, message = item
                    
                    self.progress_bar.stop()
                    self.join_button.config(state="normal")
                    self.cancel_button.config(state="normal")
                    self.domain_entry.config(state="normal")
                    self.user_entry.config(state="normal")
                    self.password_entry.config(state="normal")
                    self.ou_entry.config(state="normal")
                    self.test_connection_button.config(state="normal")

                    if success:
                        self._log_message('success', "✓ Unión al dominio exitosa!")
                        self._log_message('info', "Configurando sistema de login...")
                        
                        # Configurar LightDM
                        self._configure_lightdm_after_join()
                    else:
                        self._log_message('error', f"✗ Error: {message}")
                        messagebox.showerror("Error", f"Fallo al untar:\n{message}")
                    
                    return
        except queue.Empty:
            self.root.after(500, self._process_join_result)

    def _configure_lightdm_after_join(self):
        """Configura LightDM después de unirse al dominio"""
        def configure():
            configurator = LightDMConfigurator(output_callback=self._log_message)
            success, msg = configurator.configure()
            self.process_queue.put(('lightdm_result', success, msg))

        threading.Thread(target=configure, daemon=True).start()
        self.root.after(500, self._process_lightdm_result)

    def _process_lightdm_result(self):
        """Procesa el resultado de la configuración de LightDM"""
        try:
            while True:
                item = self.process_queue.get_nowait()
                if item[0] == 'lightdm_result':
                    _, success, message = item
                    
                    if success:
                        self._log_message('success', "✓ Configuración completada")
                        
                        # crear marcador pending_verify
                        try:
                            with open('/var/lib/escuela-domain-joiner/pending_verify', 'w') as f:
                                f.write(f"domain={domain}\n")
                        except Exception as e:
                            self._log_message('warning', f"No se pudo crear marcador pending_verify: {e}")

                        # Ofrecer reinicio
                        if messagebox.askyesno(
                            "Éxito",
                            f"El equipo ha sido unido exitosamente.\n\n¿Desea reiniciar ahora para aplicar los cambios?"
                        ):
                            try:
                                import subprocess
                                subprocess.run(['pkexec', 'reboot'], check=True)
                            except Exception as e:
                                messagebox.showerror(
                                    "Error de reinicio",
                                    f"No se pudo reiniciar automáticamente.\n{e}\n\nPor favor reinita manualmente."
                                )
                        else:
                            self._log_message('info', "Reinicio pospuesto. Reinita manualmente después.")
                            self._update_domain_state(True, self.domain_entry.get().strip())
                    else:
                        self._log_message('warning', f"Advertencia: {message}")
                        messagebox.showwarning("Advertencia", f"Se completó la unión pero con advertencias.\n{message}")
                    
                    return
        except queue.Empty:
            self.root.after(500, self._process_lightdm_result)

    def _leave_domain(self):
        """Desunirse del dominio"""
        if not self.is_joined or not self.current_domain:
            messagebox.showerror("Error", "No hay dominio configurado")
            return

        # Confirmación
        if not messagebox.askyesno(
            "Confirmação",
            f"¿Está seguro de que desea desuntar del dominio {self.current_domain}?\n\nSe requiere reinicio."
        ):
            return

        self.join_button.config(state="disabled")
        self.leave_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.progress_bar.start()

        self._log_message('info', f"Removiendo equipo del dominio: {self.current_domain}")

        def leave():
            leaver = DomainLeaver(output_callback=self._log_message)
            success, msg = leaver.leave(self.current_domain)
            self.process_queue.put(('leave_result', success, msg))

        threading.Thread(target=leave, daemon=True).start()
        self.root.after(500, self._process_leave_result)

    def _process_leave_result(self):
        """Procesa el resultado de la desunión"""
        try:
            while True:
                item = self.process_queue.get_nowait()
                if item[0] == 'leave_result':
                    _, success, message = item
                    
                    self.progress_bar.stop()
                    self.join_button.config(state="normal")
                    self.leave_button.config(state="normal")
                    self.cancel_button.config(state="normal")

                    if success:
                        self._log_message('success', "✓ Desunión completada")
                        
                        if messagebox.askyesno(
                            "Éxito",
                            "El equipo ha sido removido del dominio.\n\n¿Desea reiniciar ahora?"
                        ):
                            try:
                                import subprocess
                                subprocess.run(['pkexec', 'reboot'], check=True)
                            except Exception as e:
                                messagebox.showerror(
                                    "Error de reinicio",
                                    f"No se pudo reiniciar automáticamente.\n{e}"
                                )
                        
                        # Actualizar estado
                        self._check_initial_state()
                    else:
                        self._log_message('error', f"✗ Error: {message}")
                        messagebox.showerror("Error", f"Fallo al desuntar:\n{message}")
                    
                    return
        except queue.Empty:
            self.root.after(500, self._process_leave_result)


def main():
    root = tk.Tk()
    app = DomainJoinerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
