import socket
import pickle
from config import *

class NetworkManager:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.es_host = False
        self.conectado = False
        
        # Timeout para que las operaciones no se queden colgadas eternamente
        self.sock.settimeout(0.001) 

    def hostear(self):
        """Inicia el modo Servidor sin congelar la ventana"""
        import pygame # Necesario para el truco anti-freeze
        
        try:
            # Aseguramos que el socket esté limpio
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(("0.0.0.0", PUERTO))
            self.sock.listen(1)
            self.es_host = True
            
            print("Esperando jugador... (La ventana seguirá respondiendo)")
            
            self.sock.setblocking(False) # Importante: No bloquear
            
            esperando = True
            while esperando:
                # TRUCO MAESTRO:
                # Procesamos eventos de Pygame para que la ventana no se ponga blanca
                # y el sistema operativo sepa que el programa sigue funcionando.
                pygame.event.pump() 
                
                try:
                    # Intentamos aceptar conexión
                    self.conn, addr = self.sock.accept()
                    
                    # ¡Si pasa de aquí, es que alguien entró!
                    self.conn.setblocking(False)
                    self.conectado = True
                    print(f"¡Conectado con {addr}!")
                    return True
                    
                except BlockingIOError:
                    # Nadie se ha conectado aún, seguimos dando vueltas en el bucle
                    pass
                except Exception as e:
                    print(f"Error inesperado: {e}")
                    return False
                    
        except Exception as e:
            print(f"Error al intentar hostear: {e}")
            return False

    def conectar(self, ip):
        """Inicia el modo Cliente"""
        try:
            print(f"Intentando conectar a {ip}...")
            # Ponemos blocking temporalmente para el saludo inicial
            self.sock.setblocking(True) 
            self.sock.settimeout(5) # Esperar máximo 5 segundos
            
            self.sock.connect((ip, PUERTO))
            
            self.sock.setblocking(False)
            self.es_host = False
            self.conectado = True
            print("¡Conexión exitosa!")
            return True
        except Exception as e:
            print(f"Error conectando: {e}")
            return False

    def enviar(self, data):
        """Envía cualquier objeto Python serializado"""
        if not self.conectado: return
        try:
            paquete = pickle.dumps(data)
            socket_dest = self.conn if self.es_host else self.sock
            socket_dest.sendall(paquete)
        except BlockingIOError: pass
        except Exception as e: print(f"Error enviando: {e}")

    def recibir(self):
        """Intenta recibir datos. Si no hay, retorna None"""
        if not self.conectado: return None
        try:
            socket_source = self.conn if self.es_host else self.sock
            data = socket_source.recv(BUFF_SIZE)
            if not data: return None
            return pickle.loads(data)
        except BlockingIOError: return None
        except Exception: return None