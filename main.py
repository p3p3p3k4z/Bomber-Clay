import pygame
import sys
import os
from config import *
from game.gamestate import GameState
from game.entities import Jugador
from network.manager import NetworkManager
from ui.renderer import Renderer

def main():
    pygame.init()
    pygame.mixer.init() # SISTEMA DE AUDIO ACTIVADO
    
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("ECO-BOMBER: FINAL EDITION")
    clock = pygame.time.Clock()
    
    # --- CARGAR SONIDOS ---
    sonidos = {}
    try:
        # Carga segura: No falla si falta el archivo
        if os.path.exists("assets/explosion.mp3"):
            sonidos["EXPLOSION"] = pygame.mixer.Sound("assets/explosion.mp3")
            sonidos["EXPLOSION"].set_volume(0.5)
            
        if os.path.exists("assets/hit.wav"):
            sonidos["ENEMY_DIE"] = pygame.mixer.Sound("assets/hit.wav")
            sonidos["DEATH_PLAYER"] = pygame.mixer.Sound("assets/hit.wav")
        
        # Música
        if os.path.exists("assets/musica.mp3"):
            pygame.mixer.music.load("assets/musica.mp3")
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1) # Loop infinito
            print("[AUDIO] Música iniciada")
    except Exception as e:
        print(f"[AUDIO] Error cargando sonidos: {e}")

    net = NetworkManager()
    renderer = Renderer(pantalla)
    
    # --- MENÚ PRINCIPAL ---
    font = pygame.font.SysFont("Impact", 50)
    font_s = pygame.font.SysFont("Consolas", 24)
    modo = None
    input_ip = "127.0.0.1"
    
    en_menu = True
    while en_menu:
        pantalla.fill(NEGRO)
        
        # Dibujar Menú
        t = pygame.time.get_ticks() / 500
        color_titulo = (0, 255, 0) if int(t)%2==0 else (50, 255, 50)
        titulo = font.render("ECO-BOMBER", True, color_titulo)
        pantalla.blit(titulo, (ANCHO//2 - 120, 80))
        
        op1 = font_s.render("[1] JUGAR SOLO (OFFLINE)", True, BLANCO)
        op2 = font_s.render("[H] CREAR SALA (HOST)", True, AZUL_J1)
        op3 = font_s.render("[C] CONECTAR (CLIENTE)", True, ROJO_J2)
        ip_txt = font_s.render(f"IP DEL HOST: {input_ip}", True, (150,150,150))
        
        pantalla.blit(op1, (200, 200))
        pantalla.blit(op2, (200, 250))
        pantalla.blit(op3, (200, 300))
        pantalla.blit(ip_txt, (200, 400))
        
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1: modo = "SOLO"; en_menu = False
                if e.key == pygame.K_h: 
                    if net.hostear(): modo = "HOST"; en_menu = False
                if e.key == pygame.K_c: 
                    if net.conectar(input_ip): modo = "CLIENT"; en_menu = False
                
                if e.key == pygame.K_BACKSPACE: input_ip = input_ip[:-1]
                elif len(input_ip)<15 and e.unicode in "0123456789.": input_ip += e.unicode

    # --- INICIALIZAR ESTADO ---
    mi_id = "P1" if modo == "SOLO" else str(net.sock.getsockname()[1])
    
    if modo in ["HOST", "SOLO"]:
        estado = GameState(modo_singleplayer=(modo=="SOLO"))
        estado.jugadores[mi_id] = Jugador(mi_id, 1, 1, AZUL_J1)
    else:
        estado = None

    # --- BUCLE DE JUEGO ---
    running = True
    while running:
        clock.tick(FPS)
        
        # 1. INPUTS
        accion = None
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                
                # Controles
                if e.key == pygame.K_UP: accion = ("MOV", 0, -1)
                elif e.key == pygame.K_DOWN: accion = ("MOV", 0, 1)
                elif e.key == pygame.K_LEFT: accion = ("MOV", -1, 0)
                elif e.key == pygame.K_RIGHT: accion = ("MOV", 1, 0)
                elif e.key == pygame.K_SPACE: accion = ("BOMBA",)

        # 2. LÓGICA + RED + AUDIO
        lista_eventos_audio = []

        if modo == "SOLO":
            if accion:
                if accion[0] == "MOV": estado.mover_jugador(mi_id, accion[1], accion[2])
                if accion[0] == "BOMBA": estado.poner_bomba(mi_id)
            estado.update()
            lista_eventos_audio = estado.audio_events[:]
            estado.audio_events = [] 

        elif modo == "HOST":
            try: # Recibir Cliente
                d = net.recibir()
                if d:
                    cid, cact = d["id"], d["accion"]
                    if cid not in estado.jugadores:
                        estado.jugadores[cid] = Jugador(cid, COLS-2, FILAS-2, ROJO_J2)
                    if cact:
                        if cact[0] == "MOV": estado.mover_jugador(cid, cact[1], cact[2])
                        if cact[0] == "BOMBA": estado.poner_bomba(cid)
            except: pass
            
            # Mis acciones
            if accion:
                if accion[0] == "MOV": estado.mover_jugador(mi_id, accion[1], accion[2])
                if accion[0] == "BOMBA": estado.poner_bomba(mi_id)
            
            estado.update()
            lista_eventos_audio = estado.audio_events[:]
            
            # Enviar al cliente (incluyendo los eventos de audio)
            net.enviar(estado)
            estado.audio_events = [] 

        elif modo == "CLIENT":
            net.enviar({"id": mi_id, "accion": accion})
            nuevo = net.recibir()
            if nuevo: 
                estado = nuevo
                # El cliente reproduce los sonidos que dicta el servidor
                lista_eventos_audio = estado.audio_events

        # 3. REPRODUCIR SONIDOS
        for evento in lista_eventos_audio:
            if evento in sonidos:
                sonidos[evento].play()
            elif evento == "POWERUP":
                pass # Aquí puedes poner un sonido extra si quieres

        # 4. DIBUJAR
        if estado:
            renderer.dibujar_juego(estado, mi_id)
            if estado.estado_partida in ["WIN", "LOSE"]:
                renderer.dibujar_mensaje_final(estado.estado_partida, estado.jugadores)
        else:
            pantalla.fill(NEGRO)
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()