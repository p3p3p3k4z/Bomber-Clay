import pygame
import sys
import os
import random
from config import *
from game.gamestate import GameState
from game.entities import Jugador
from network.manager import NetworkManager
from ui.renderer import Renderer

def reproducir_musica_nivel(nivel):
    """Selecciona música aleatoria o tema de jefe"""
    pygame.mixer.music.stop()
    track = None
    
    if nivel == 3: # Nivel Jefe
        if os.path.exists("assets/music_boss.mp3"): track = "assets/music_boss.mp3"
        elif os.path.exists("assets/musica.mp3"): track = "assets/musica.mp3"
    else: # Niveles normales (Aleatorio)
        posibles = []
        if os.path.exists("assets/music_1.mp3"): posibles.append("assets/music_1.mp3")
        if os.path.exists("assets/music_2.mp3"): posibles.append("assets/music_2.mp3")
        if os.path.exists("assets/musica.mp3"): posibles.append("assets/musica.mp3")
        
        if posibles: track = random.choice(posibles)
    
    if track:
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play(-1)
        except: pass

def main():
    pygame.init()
    pygame.mixer.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("ECO-BOMBER: FINAL EDITION")
    clock = pygame.time.Clock()
    
    # Audio FX
    sonidos = {}
    try:
        if os.path.exists("assets/explosion.mp3"): sonidos["EXPLOSION"] = pygame.mixer.Sound("assets/explosion.mp3")
        if os.path.exists("assets/hit.wav"): sonidos["ENEMY_DIE"] = pygame.mixer.Sound("assets/hit.wav")
    except: pass

    net = NetworkManager()
    renderer = Renderer(pantalla)
    
    # --- CICLO APLICACIÓN ---
    while True:
        # 1. MENU
        modo = None
        input_ip = "127.0.0.1"
        nombre_jugador = ""
        en_menu = True
        
        if os.path.exists("assets/intro.mp3"):
            pygame.mixer.music.load("assets/intro.mp3")
            pygame.mixer.music.play(-1)

        while en_menu:
            if renderer.assets.get("intro_bg"): pantalla.blit(renderer.assets["intro_bg"], (0,0))
            else: pantalla.fill(NEGRO)
            
            mx, my = pygame.mouse.get_pos()
            click = False
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); sys.exit()
                if e.type==pygame.MOUSEBUTTONDOWN: click=True
                if e.type==pygame.KEYDOWN:
                    if e.key==pygame.K_BACKSPACE: input_ip = input_ip[:-1]
                    elif len(input_ip)<15: input_ip += e.unicode

            bh = pygame.Rect(250, 250, 300, 50)
            bc = pygame.Rect(250, 320, 300, 50)
            bs = pygame.Rect(250, 390, 300, 50)
            
            renderer.dibujar_boton("CREAR SALA", 250, 250, 300, 50, bh.collidepoint(mx,my))
            renderer.dibujar_boton("UNIRSE A IP", 250, 320, 300, 50, bc.collidepoint(mx,my))
            renderer.dibujar_boton("SOLITARIO", 250, 390, 300, 50, bs.collidepoint(mx,my))
            
            txt = renderer.font.render(f"IP: {input_ip}", True, BLANCO)
            pantalla.blit(txt, (300, 460))

            if click:
                if bh.collidepoint(mx,my): 
                    if net.hostear(): modo="HOST"; en_menu=False
                if bc.collidepoint(mx,my): 
                    if net.conectar(input_ip): modo="CLIENT"; en_menu=False
                if bs.collidepoint(mx,my): modo="SOLO"; en_menu=False
            
            pygame.display.flip()

        # 2. INICIO JUEGO
        mi_id = "P1" if modo=="SOLO" else str(net.sock.getsockname()[1])
        if modo in ["HOST", "SOLO"]:
            estado = GameState(modo_singleplayer=(modo=="SOLO"))
            estado.jugadores[mi_id] = Jugador(mi_id, 1, 1, AZUL_J1)
            # Reproducir música inicial
            reproducir_musica_nivel(1)
        else:
            estado = None

        # 3. GAME LOOP
        running = True
        while running:
            clock.tick(FPS)
            accion = None
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if estado and estado.estado_partida in [STATE_WIN, STATE_GAMEOVER]:
                        if e.key == pygame.K_RETURN: estado.estado_partida = STATE_INPUT_NAME
                        if e.key == pygame.K_ESCAPE: running = False
                    elif estado and estado.estado_partida == STATE_INPUT_NAME:
                        if e.key == pygame.K_RETURN:
                            if modo in ["HOST","SOLO"]: 
                                estado.guardar_puntaje(nombre_jugador, estado.jugadores[mi_id].score)
                            estado.estado_partida = STATE_SCOREBOARD
                        elif e.key == pygame.K_BACKSPACE: nombre_jugador = nombre_jugador[:-1]
                        elif len(nombre_jugador)<10: nombre_jugador += e.unicode
                    else:
                        if e.key==pygame.K_UP: accion=("MOV",0,-1)
                        if e.key==pygame.K_DOWN: accion=("MOV",0,1)
                        if e.key==pygame.K_LEFT: accion=("MOV",-1,0)
                        if e.key==pygame.K_RIGHT: accion=("MOV",1,0)
                        if e.key==pygame.K_SPACE: accion=("BOMBA",)

            eventos_audio = []
            
            if modo == "SOLO":
                if estado.estado_partida == STATE_PLAYING:
                    if accion:
                        if accion[0]=="MOV": estado.mover_jugador(mi_id, accion[1], accion[2])
                        if accion[0]=="BOMBA": estado.poner_bomba(mi_id)
                    estado.update()
                    eventos_audio = estado.audio_events[:]
                    estado.audio_events = []
                elif estado.estado_partida == STATE_NEXT_LEVEL:
                    # Cambio de música y nivel
                    reproducir_musica_nivel(estado.nivel_actual)
                    estado.estado_partida = STATE_PLAYING

            elif modo == "HOST":
                if estado.estado_partida == STATE_PLAYING:
                    try:
                        d = net.recibir()
                        if d:
                            if d["id"] not in estado.jugadores: estado.jugadores[d["id"]] = Jugador(d["id"],1,1,ROJO_J2)
                            if d["accion"]:
                                if d["accion"][0]=="MOV": estado.mover_jugador(d["id"], d["accion"][1], d["accion"][2])
                                if d["accion"][0]=="BOMBA": estado.poner_bomba(d["id"])
                    except: pass
                    if accion:
                        if accion[0]=="MOV": estado.mover_jugador(mi_id, accion[1], accion[2])
                        if accion[0]=="BOMBA": estado.poner_bomba(mi_id)
                    estado.update()
                    eventos_audio = estado.audio_events[:]
                    net.enviar(estado)
                    estado.audio_events = []
                elif estado.estado_partida == STATE_NEXT_LEVEL:
                    reproducir_musica_nivel(estado.nivel_actual)
                    estado.estado_partida = STATE_PLAYING
                    net.enviar(estado)

            elif modo == "CLIENT":
                net.enviar({"id": mi_id, "accion": accion})
                new = net.recibir()
                if new: 
                    # Detectar cambio de música si el nivel cambió
                    if estado and new.nivel_actual != estado.nivel_actual:
                        reproducir_musica_nivel(new.nivel_actual)
                    estado = new
                    eventos_audio = estado.audio_events

            for ev in eventos_audio:
                if ev in sonidos: sonidos[ev].play()

            if estado:
                renderer.dibujar_juego(estado, mi_id)
                if estado.estado_partida in [STATE_WIN, STATE_GAMEOVER]:
                    renderer.dibujar_mensaje_final("WIN" if estado.estado_partida==STATE_WIN else "LOSE", estado.jugadores)
                if estado.estado_partida == STATE_INPUT_NAME:
                    s=pygame.Surface((ANCHO,ALTO), pygame.SRCALPHA); s.fill((0,0,0,220)); pantalla.blit(s,(0,0))
                    t1=renderer.font_big.render("NOMBRE:", True, BLANCO)
                    t2=renderer.font_big.render(f"> {nombre_jugador} <", True, AZUL_J1)
                    pantalla.blit(t1, (250, 100)); pantalla.blit(t2, (250, 250))
                if estado.estado_partida == STATE_SCOREBOARD:
                    s=pygame.Surface((ANCHO,ALTO)); s.fill(NEGRO); pantalla.blit(s,(0,0))
                    sc = estado.cargar_puntajes()
                    y=100
                    pantalla.blit(renderer.font_big.render("RANKING", True, DORADO), (300, 20))
                    for l in sc:
                        pantalla.blit(renderer.font.render(f"{l['nombre']}: {l['score']}", True, BLANCO), (300, y)); y+=40
                    
                    t_esc = renderer.font.render("ESC PARA MENU", True, ROJO_J2)
                    pantalla.blit(t_esc, (300, 550))
                    if pygame.key.get_pressed()[pygame.K_ESCAPE]: running = False
            else:
                pantalla.fill(NEGRO)
            
            pygame.display.flip()
        
        # Limpieza al volver al menú
        net.conn = None
        net.conectado = False

if __name__ == "__main__":
    main()