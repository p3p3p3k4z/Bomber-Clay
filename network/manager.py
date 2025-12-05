import socket
import pickle
from config import *

class NetworkManager:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.es_host = False
        self.conectado = False
        
        # Importante: Desactivar bloqueo para que el juego no se congele
        # si no llegan datos en un frame.
        self.sock.settimeout(None) 

    def hostear(self):
        """Inicia el modo Servidor"""
        try:
            self.sock.bind(("0.0.0.0", PUERTO))
            self.sock.listen(1)
            self.es_host = True
            print("Esperando conexión...")
            # Aquí sí bloqueamos esperando al cliente
            self.sock.setblocking(True) 
            self.conn, addr = self.sock.accept()
            self.conn.setblocking(False) # Ya conectado, desbloqueamos
            self.conectado = True
            return True
        except Exception as e:
            print(f"Error hosting: {e}")
            return False

    def conectar(self, ip):
        """Inicia el modo Cliente"""
        try:
            self.sock.setblocking(True)
            self.sock.connect((ip, PUERTO))
            self.sock.setblocking(False)
            self.es_host = False
            self.conectado = True
            return True
        except Exception as e:
            print(f"Error conectando: {e}")
            return False

    def enviar(self, data):
        """Envía cualquier objeto Python serializado"""
        try:
            paquete = pickle.dumps(data)
            socket_dest = self.conn if self.es_host else self.sock
            socket_dest.sendall(paquete)
        except BlockingIOError: pass
        except Exception as e: print(f"Error enviando: {e}")

    def recibir(self):
        """Intenta recibir datos. Si no hay, retorna None (no bloquea)"""
        try:
            socket_source = self.conn if self.es_host else self.sock
            data = socket_source.recv(BUFF_SIZE)
            if not data: return None
            return pickle.loads(data)
        except BlockingIOError: return None
        except Exception: return None