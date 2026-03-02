"""
Módulo para manejar la desunión de un equipo de un dominio
"""

import subprocess
from .logger import logger


class DomainLeaver:
    """
    Ejecuta el comando realm leave para desunir el equipo del dominio
    """
    
    def __init__(self, output_callback=None):
        """
        output_callback: función para mostrar output en tiempo real
        """
        self.output_callback = output_callback or self._default_callback
    
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
    
    def leave(self, domain):
        """
        Ejecuta realm leave para el dominio especificado
        
        Args:
            domain: Nombre del dominio
        
        Returns:
            (éxito, mensaje)
        """
        process = None
        try:
            self._log_output('info', f"Desuniendo del dominio: {domain}")
            
            cmd = ['pkexec', 'realm', 'leave', '--verbose', domain]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            with process.stdout as stdout:
                for line in stdout:
                    line = line.rstrip('\n')
                    if line:
                        output_lines.append(line)
                        self._log_output('info', line)

            returncode = process.wait()
            
            if returncode == 0:
                self._log_output('success', f"✓ Desunión del dominio '{domain}' EXITOSA")
                logger.info(f"realm leave completado exitosamente para: {domain}")
                return True, domain
            else:
                error_msg = '\n'.join(output_lines)
                if not error_msg:
                    error_msg = f"Error desconocido (código: {returncode})"
                
                self._log_output('error', error_msg)
                logger.error(f"realm leave falló para {domain}: {error_msg}")
                return False, error_msg
        
        except FileNotFoundError:
            msg = "Comando 'realm' o 'pkexec' no encontrado"
            self._log_output('error', msg)
            logger.error(msg)
            return False, msg
        
        except Exception as e:
            msg = f"Error inesperado: {str(e)}"
            self._log_output('error', msg)
            logger.error(msg)
            if process:
                process.kill()
            return False, msg
