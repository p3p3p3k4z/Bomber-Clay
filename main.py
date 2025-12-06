import pygame
import sys
import os
from config import *
from game.gamestate import GameState
from game.entities import Jugador
from network.manager import NetworkManager
from ui.renderer import Renderer
from utils.asset_manager import AssetManager

def main():
    pygame.init()
    pygame.mixer.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("ECO-BOMBER: FINAL EDITION")
    clock = pygame.time.Clock()
    
    # 1. Carga de Assets una sola vez
    assets = AssetManager()
    renderer = Renderer(pantalla, assets)
    
    # --- BUCLE MAESTRO ---
    while True:
        net = NetworkManager()
        modo = None
        input_ip = "127.0.0.1"
        nombre_jugador = ""
        en_menu = True
        
        assets.reproducir_musica("INTRO")

        # --- BUCLE DEL MENÚ ---
        while en_menu:
            if assets.images.get("intro_bg"): pantalla.blit(assets.images["intro_bg"], (0,0))
            else: pantalla.fill(NEGRO)
            
            mx, my = pygame.mouse.get_pos()
            click = False
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN: click = True
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_BACKSPACE: input_ip = input_ip[:-1]
                    elif len(input_ip) < 15: input_ip += e.unicode

            # Botones
            bh = pygame.Rect(250, 250, 300, 50)
            bc = pygame.Rect(250, 320, 300, 50)
            bs = pygame.Rect(250, 390, 300, 50)
            
            renderer.dibujar_boton("CREAR SALA", 250, 250, 300, 50, bh.collidepoint(mx,my))
            renderer.dibujar_boton("UNIRSE A IP", 250, 320, 300, 50, bc.collidepoint(mx,my))
            renderer.dibujar_boton("SOLITARIO", 250, 390, 300, 50, bs.collidepoint(mx,my))
            
            txt = assets.fonts["ui"].render(f"IP: {input_ip}", True, BLANCO)
            pantalla.blit(txt, (300, 460))

            if click:
                if bh.collidepoint(mx,my): 
                    if net.hostear(): modo = "HOST"; en_menu = False
                if bc.collidepoint(mx,my): 
                    if net.conectar(input_ip): modo = "CLIENT"; en_menu = False
                if bs.collidepoint(mx,my): modo = "SOLO"; en_menu = False
            pygame.display.flip()

        # --- INICIO DE PARTIDA ---
        assets.reproducir_musica(1)
        mi_id = "P1" if modo == "SOLO" else str(net.sock.getsockname()[1])
        estado = None
        if modo in ["HOST", "SOLO"]:
            estado = GameState(modo_singleplayer=(modo=="SOLO"))
            estado.jugadores[mi_id] = Jugador(mi_id, 1, 1, AZUL_J1)

        # --- BUCLE DE JUEGO ---
        running = True
        while running:
            clock.tick(FPS)
            accion = None
            events = pygame.event.get()
            mx, my = pygame.mouse.get_pos()
            click_trofeo = False

            for e in events:
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN: click_trofeo = True
                
                if e.type == pygame.KEYDOWN:
                    # SALIDA DE EMERGENCIA
                    if e.key == pygame.K_ESCAPE and estado and estado.estado_partida != STATE_SCOREBOARD:
                        running = False 

                    # LÓGICA DE ESTADOS
                    # 1. Jugando -> Pausa
                    if estado and estado.estado_partida == STATE_PLAYING:
                        if e.key == pygame.K_p: estado.estado_partida = STATE_PAUSE
                        # Inputs de juego
                        elif e.key == pygame.K_UP: accion = ("MOV", 0, -1)
                        elif e.key == pygame.K_DOWN: accion = ("MOV", 0, 1)
                        elif e.key == pygame.K_LEFT: accion = ("MOV", -1, 0)
                        elif e.key == pygame.K_RIGHT: accion = ("MOV", 1, 0)
                        elif e.key == pygame.K_SPACE: accion = ("BOMBA",)

                    # 2. Pausa -> Jugando
                    elif estado and estado.estado_partida == STATE_PAUSE:
                        if e.key == pygame.K_p: estado.estado_partida = STATE_PLAYING
                        if e.key == pygame.K_ESCAPE: running = False

                    # 3. Game Over / Victoria -> Input Nombre
                    elif estado and estado.estado_partida in [STATE_GAMEOVER, STATE_WIN]:
                        if e.key == pygame.K_RETURN: 
                            estado.estado_partida = STATE_INPUT_NAME

                    elif estado and estado.estado_partida == STATE_INPUT_NAME:
                        if e.key == pygame.K_RETURN:
                            if modo in ["HOST", "SOLO"]:
                                # Guardar puntaje propio
                                if mi_id in estado.jugadores:
                                    pts = estado.jugadores[mi_id].score
                                    estado.guardar_puntaje(nombre_jugador if nombre_jugador else "Anonimo", pts)
                            
                            # CAMBIO DE ESTADO A SCOREBOARD
                            estado.estado_partida = STATE_SCOREBOARD
                            
                            # REPRODUCIR MÚSICA DE RANKING (NUEVO)
                            assets.reproducir_musica("RANKING") 

                        elif e.key == pygame.K_BACKSPACE:
                            nombre_jugador = nombre_jugador[:-1]
                        elif len(nombre_jugador) < 12:
                            nombre_jugador += e.unicode

                    # 4. Input Nombre -> Guardar -> Scoreboard
                    elif estado and estado.estado_partida == STATE_INPUT_NAME:
                        if e.key == pygame.K_RETURN:
                            if modo in ["HOST", "SOLO"]:
                                # Guardar puntaje propio
                                if mi_id in estado.jugadores:
                                    pts = estado.jugadores[mi_id].score
                                    estado.guardar_puntaje(nombre_jugador if nombre_jugador else "Anonimo", pts)
                            estado.estado_partida = STATE_SCOREBOARD
                        elif e.key == pygame.K_BACKSPACE:
                            nombre_jugador = nombre_jugador[:-1]
                        elif len(nombre_jugador) < 12:
                            nombre_jugador += e.unicode

                    # 5. Scoreboard -> Salir
                    elif estado and estado.estado_partida == STATE_SCOREBOARD:
                        if e.key == pygame.K_ESCAPE:
                            running = False # Vuelve al menú principal

                    # 6. Transición de Nivel
                    elif estado and estado.estado_partida == STATE_LEVEL_COMPLETED:
                        if e.key == pygame.K_RETURN:
                            if modo in ["HOST", "SOLO"]:
                                estado.nivel_actual += 1
                                estado.cargar_nivel(estado.nivel_actual)
                                estado.estado_partida = STATE_PLAYING
                                assets.reproducir_musica(estado.nivel_actual)

            # --- ACTUALIZACIÓN ---
            eventos_audio = []
            if modo == "SOLO":
                if estado.estado_partida == STATE_PLAYING:
                    if accion:
                        if accion[0] == "MOV": estado.mover_jugador(mi_id, accion[1], accion[2])
                        if accion[0] == "BOMBA": estado.poner_bomba(mi_id)
                    estado.update()
                    eventos_audio = estado.audio_events[:]
                    estado.audio_events = [] 
            elif modo == "HOST":
                try:
                    d = net.recibir()
                    if d:
                        cid, cact = d["id"], d["accion"]
                        if cid not in estado.jugadores:
                            estado.jugadores[cid] = Jugador(cid, 1, 1, ROJO_J2)
                        if cact and estado.estado_partida == STATE_PLAYING:
                            if cact[0] == "MOV": estado.mover_jugador(d["id"], d["accion"][1], d["accion"][2])
                            if cact[0] == "BOMBA": estado.poner_bomba(d["id"])
                except: pass
                if estado.estado_partida == STATE_PLAYING and accion:
                    if accion[0] == "MOV": estado.mover_jugador(mi_id, accion[1], accion[2])
                    if accion[0] == "BOMBA": estado.poner_bomba(mi_id)
                estado.update()
                eventos_audio = estado.audio_events[:]
                estado.audio_events = []
                net.enviar(estado)
            elif modo == "CLIENT":
                net.enviar({"id": mi_id, "accion": accion})
                new = net.recibir()
                if new: 
                    if estado and new.nivel_actual != estado.nivel_actual:
                        assets.reproducir_musica(new.nivel_actual)
                    estado = new
                    eventos_audio = estado.audio_events

            for evento in eventos_audio: assets.reproducir_sonido(evento)

            if estado:
                renderer.dibujar_juego(estado, mi_id)
                if estado.estado_partida == STATE_PAUSE: renderer.dibujar_pausa()
                elif estado.estado_partida == STATE_LEVEL_COMPLETED: renderer.dibujar_nivel_completado(estado.nivel_actual)
                elif estado.estado_partida == STATE_WIN:
                    rect = renderer.dibujar_victoria_trofeo()
                    if click_trofeo and rect.collidepoint(mx, my): estado.estado_partida = STATE_INPUT_NAME
                elif estado.estado_partida == STATE_GAMEOVER: renderer.dibujar_mensaje_final("LOSE", estado.jugadores)
                elif estado.estado_partida == STATE_INPUT_NAME: renderer.dibujar_input_nombre(nombre_jugador)
                elif estado.estado_partida == STATE_SCOREBOARD:
                    scores = estado.cargar_puntajes()
                    renderer.dibujar_tabla_puntajes(scores)
            else: pantalla.fill(NEGRO)
            
            pygame.display.flip()
        
        if net.conn: 
            try: net.conn.close() 
            except: pass
        if net.sock: 
            try: net.sock.close() 
            except: pass

if __name__ == "__main__":
    main()