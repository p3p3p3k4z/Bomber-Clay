import pygame
import sys
import time
from config import *
from game.gamestate import GameState
from game.entities import Jugador
from network.manager import NetworkManager
from ui.renderer import Renderer

def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("ECO-BOMBER: NEON ROOTS")
    clock = pygame.time.Clock()
    
    # Inicializar módulos
    net = NetworkManager()
    renderer = Renderer(pantalla)
    
    # --- FASE 1: MENÚ DE CONEXIÓN ---
    font = pygame.font.SysFont("Impact", 40)
    font_small = pygame.font.SysFont("Consolas", 20)
    
    modo = None
    input_ip = "127.0.0.1"
    
    while not net.conectado:
        pantalla.fill(NEGRO)
        
        # Dibujar título neón
        t = time.time()
        color_titulo = COLOR_NEON_VERDE()
        txt_titulo = font.render("ECO-BOMBER", True, color_titulo)
        
        # Opciones
        txt_h = font_small.render("[H]OSTEAR PARTIDA (SER ANFITRIÓN)", True, BLANCO)
        txt_c = font_small.render("[C]ONECTAR COMO CLIENTE", True, AZUL_J1)
        
        # Input IP
        color_ip = (0, 255, 255) if modo == "CLIENT" else (100, 100, 100)
        txt_ip = font_small.render(f"IP DEL HOST: {input_ip}_", True, color_ip)
        
        pantalla.blit(txt_titulo, (ANCHO//2 - 100, 100))
        pantalla.blit(txt_h, (150, 250))
        pantalla.blit(txt_c, (150, 300))
        pantalla.blit(txt_ip, (150, 350))
        
        if modo == "HOST_WAITING":
            txt_wait = font.render("ESPERANDO RIVAL...", True, (255, 255, 0))
            pantalla.blit(txt_wait, (ANCHO//2 - 150, 500))

        pygame.display.flip()

        # Eventos del Menú
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_h:
                    modo = "HOST_WAITING"
                    # Renderizamos un frame de espera antes de bloquear
                    pantalla.fill(NEGRO)
                    pantalla.blit(font.render("INICIANDO SERVIDOR...", True, BLANCO), (200, 300))
                    pygame.display.flip()
                    
                    if net.hostear():
                        modo = "HOST"
                        
                if e.key == pygame.K_c:
                    # Intentar conectar
                    pantalla.fill(NEGRO)
                    pantalla.blit(font.render(f"CONECTANDO A {input_ip}...", True, BLANCO), (200, 300))
                    pygame.display.flip()
                    
                    if net.conectar(input_ip):
                        modo = "CLIENT"
                    else:
                        input_ip = "ERROR DE CONEXIÓN"
                
                # Escribir IP
                if e.key == pygame.K_BACKSPACE:
                    input_ip = input_ip[:-1]
                elif len(input_ip) < 15:
                    if e.unicode in "0123456789.":
                        if input_ip == "127.0.0.1": input_ip = "" # Limpiar default al escribir
                        input_ip += e.unicode

    # --- FASE 2: INICIALIZACIÓN DEL JUEGO ---
    mi_id = str(net.sock.getsockname()[1])
    print(f"Juego iniciado. Mi ID: {mi_id}")

    if modo == "HOST":
        estado = GameState()
        # Agregar al Host (J1)
        estado.jugadores[mi_id] = Jugador(mi_id, 1, 1, AZUL_J1)
    else:
        estado = None # El cliente espera recibir el primer estado

    # --- FASE 3: BUCLE PRINCIPAL (GAME LOOP) ---
    running = True
    while running:
        clock.tick(FPS)
        
        # 1. INPUTS (TECLADO)
        accion = None
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            
            if e.type == pygame.KEYDOWN:
                # Movimiento (Flechas)
                if e.key == pygame.K_UP: accion = ("MOV", 0, -1)
                elif e.key == pygame.K_DOWN: accion = ("MOV", 0, 1)
                elif e.key == pygame.K_LEFT: accion = ("MOV", -1, 0)
                elif e.key == pygame.K_RIGHT: accion = ("MOV", 1, 0)
                # Bomba (Espacio)
                elif e.key == pygame.K_SPACE: accion = ("BOMBA",)

        # 2. LÓGICA Y RED
        if modo == "HOST":
            # A. Recibir datos del Cliente
            try:
                data_cliente = net.recibir()
                if data_cliente:
                    cid = data_cliente["id"]
                    c_accion = data_cliente["accion"]
                    
                    # Si el cliente es nuevo, agregarlo como J2
                    if cid not in estado.jugadores:
                        estado.jugadores[cid] = Jugador(cid, COLS-2, FILAS-2, ROJO_J2)
                    
                    # Procesar acción del cliente
                    if c_accion:
                        if c_accion[0] == "MOV": 
                            estado.mover_jugador(cid, c_accion[1], c_accion[2])
                        elif c_accion[0] == "BOMBA": 
                            estado.poner_bomba(cid)
            except Exception as e:
                print(f"Error recibiendo cliente: {e}")

            # B. Procesar mis acciones (Host)
            if accion:
                if accion[0] == "MOV": 
                    estado.mover_jugador(mi_id, accion[1], accion[2])
                elif accion[0] == "BOMBA": 
                    estado.poner_bomba(mi_id)

            # C. Actualizar Física del Mundo (Explosiones, Enemigos)
            estado.update()
            
            # D. Enviar Mundo actualizado a todos
            net.enviar(estado)

        else: # MODO CLIENTE
            # A. Enviar mis acciones al Host
            paquete = {"id": mi_id, "accion": accion}
            net.enviar(paquete)
            
            # B. Recibir estado del mundo
            nuevo_estado = net.recibir()
            if nuevo_estado:
                estado = nuevo_estado

        # 3. RENDERIZADO (DIBUJAR)
        if estado:
            renderer.dibujar_juego(estado, mi_id)
        else:
            # Pantalla de carga mientras llega el primer paquete
            pantalla.fill(NEGRO)
            txt = font_small.render("RECIBIENDO DATOS DEL MUNDO...", True, BLANCO)
            pantalla.blit(txt, (ANCHO//2 - 150, ALTO//2))
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()