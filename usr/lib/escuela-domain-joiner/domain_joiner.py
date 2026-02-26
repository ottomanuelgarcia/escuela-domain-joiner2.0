"""
Módulo para manejar la unión de un equipo a un dominio
"""

import subprocess
import threading
from .logger import logger


class DomainJoiner:
    """
    Ejecuta el comando realm join con las opciones especificadas
    """
    
    def __init__(self, output_callback=None):
        """
        output_callback: función para mostrar output en tiempo real
                        Recibe: (tipo, mensaje) donde tipo es 'info', 'success', 'warning', 'error'
        """
        self.output_callback = output_callback or self._default_callback
        self.process = None
    
    def _default_callback(self, msg_type, message):
        """Callback por defecto"""
        logger.info(f"[{msg_type}] {message}")
    
    def _log_output(self, msg_type, message):
        """Registra y envía output"""
        if msg_type == 'error':
            logger.error(message)
        elif msg_type == 'warning':
            logger.warning(message)
        else:
            logger.info(message)
        
        self.output_callback(msg_type, message)
    
    def join(self, domain, username, password, ou=None):
        """
        Ejecuta realm join con las credenciales proporcionadas
        
        Args:
            domain: Nombre del dominio (ej: escuela.edu)
            username: Usuario administrador
            password: Contraseña
            ou: Unidad Organizativa (opcional)
        
        Returns:
            (éxito, mensaje)
        """
        try:
            self._log_output('info', "Iniciando unión a dominio...")
            
            # Construir comando realm join
            cmd = ['pkexec', 'realm', 'join', '--verbose']
            
            # Añadir usuario
            cmd.append(f'--user={username}')
            
            # Añadir OU si se proporciona
            if ou and ou.strip():
                cmd.append(f'--computer-ou={ou.strip()}')
                self._log_output('info', f"Usando Unidad Organizativa: {ou}")
            
            # Añadir dominio
            cmd.append(domain)
            
            self._log_output('info', f"Conectando a dominio: {domain}")
            self._log_output('info', f"Usuario: {username}")
            
            # Ejecutar con stdin para la contraseña
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered para capturar línea por línea
                universal_newlines=True
            )
            
            # Enviar contraseña y leer output en tiempo real
            stdout_lines = []
            with self.process.stdin as stdin:
                stdin.write(password + '\n')
                stdin.flush()
            
            # Leer stdout línea por línea
            with self.process.stdout as stdout:
                for line in stdout:
                    line = line.rstrip('\n')
                    if line:
                        stdout_lines.append(line)
                        self._log_output('info', line)
            
            # Esperar a que termine el proceso
            returncode = self.process.wait()
            
            if returncode == 0:
                self._log_output('success', f"✓ Unión a dominio '{domain}' EXITOSA")
                logger.info(f"realm join completado exitosamente para: {domain}")
                return True, domain
            else:
                # Detectar tipo de error
                output_text = '\n'.join(stdout_lines)
                
                if "authentication" in output_text.lower() or "password" in output_text.lower():
                    error_msg = "Autenticación falló. Verifica usuario y contraseña."
                    self._log_output('error', error_msg)
                elif "not found" in output_text.lower() or "no such domain" in output_text.lower():
                    error_msg = f"Dominio '{domain}' no encontrado"
                    self._log_output('error', error_msg)
                else:
                    error_msg = output_text if output_text else f"Error desconocido (código: {returncode})"
                    self._log_output('error', error_msg)
                
                logger.error(f"realm join falló para {domain}: {error_msg}")
                return False, error_msg
        
        except FileNotFoundError:
            msg = "Comando 'realm' o 'pkexec' no encontrado. Instala realmd y policykit-1"
            self._log_output('error', msg)
            logger.error(msg)
            return False, msg
        
        except KeyboardInterrupt:
            msg = "Operación cancelada por el usuario"
            self._log_output('warning', msg)
            logger.warning(msg)
            if self.process:
                self.process.terminate()
            return False, msg
        
        except Exception as e:
            msg = f"Error inesperado: {str(e)}"
            self._log_output('error', msg)
            logger.error(msg)
            return False, msg
    
    def cancel(self):
        """Cancela el proceso en curso"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("Proceso de unión cancelado")
            except:
                self.process.kill()
