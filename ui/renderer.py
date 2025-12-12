import pygame
import math
import time
from config import *

class Renderer:
    def __init__(self, pantalla, asset_manager):
        self.pantalla = pantalla
        self.am = asset_manager

    def dibujar_boton(self, texto, x, y, w, h, hover=False):
        color_base = (0, 180, 0) if not hover else (50, 230, 50)
        color_sombra = (0, 80, 0)
        color_luz = (80, 255, 80)
        pygame.draw.rect(self.pantalla, color_sombra, (x, y+6, w, h), border_radius=12)
        pygame.draw.rect(self.pantalla, color_base, (x, y, w, h), border_radius=12)
        pygame.draw.rect(self.pantalla, color_luz, (x+2, y+2, w-4, h-4), 2, border_radius=10)
        txt = self.am.fonts["ui"].render(texto, True, BLANCO)
        self.pantalla.blit(txt, (x+(w-txt.get_width())//2, y+(h-txt.get_height())//2))

    def dibujar_juego(self, estado, mi_id):
        # 1. DIBUJAR FONDO
        bg = "bg_level1"
        if estado.nivel_actual == 2: bg = "bg_level2"
        if estado.nivel_actual == 3: bg = "bg_boss"
        if self.am.images.get(bg):
            self.pantalla.blit(self.am.images[bg], (0,0))
            s=pygame.Surface((ANCHO,ALTO)); s.set_alpha(60); s.fill(NEGRO)
            self.pantalla.blit(s,(0,0))
        else: self.pantalla.fill(COLOR_FONDO_DEFAULT)

        # 2. DIBUJAR MAPA (Aquí añadimos el Ítem de Fuego)
        for y in range(FILAS):
            for x in range(COLS):
                c = estado.mapa[y][x]
                r = (x*TAM_CELDA, y*TAM_CELDA)
                if c==R:
                    if self.am.images["wall"]: self.pantalla.blit(self.am.images["wall"], r)
                    else: pygame.draw.rect(self.pantalla, (100,100,100), (*r, TAM_CELDA, TAM_CELDA))
                elif c==B:
                    if self.am.images["bush"]: self.pantalla.blit(self.am.images["bush"], r)
                    else: pygame.draw.rect(self.pantalla, (0,100,0), (*r, TAM_CELDA, TAM_CELDA))
                elif c>=ITEM_BOMBA:
                    # ### CAMBIO AQUI 1: Lógica para pintar el Ítem Fuego ###
                    k = "item_bomb"
                    if c == ITEM_VELOCIDAD: k = "item_speed"
                    elif c == ITEM_ESCUDO: k = "item_shield"
                    elif c == ITEM_FUEGO: k = "item_fire" # <--- NUEVO
                    # -----------------------------------------------------

                    if self.am.images.get(k): self.pantalla.blit(self.am.images[k], r)
                    else: pygame.draw.circle(self.pantalla, (255,255,0), (r[0]+25,r[1]+25), 10)

        # 3. DIBUJAR BOMBAS
        for b in estado.bombas:
            pos = (b.x*TAM_CELDA, b.y*TAM_CELDA)
            if self.am.images["bomb"]:
                img = pygame.transform.scale(self.am.images["bomb"], (TAM_CELDA, TAM_CELDA))
                self.pantalla.blit(img, pos)
            else: pygame.draw.circle(self.pantalla, BLANCO, (pos[0]+25, pos[1]+25), 20)

        # 4. DIBUJAR EXPLOSIONES
        for e in estado.explosiones:
            for (ex,ey) in e.celdas:
                pos = (ex*TAM_CELDA, ey*TAM_CELDA)
                if self.am.images["fire"]: self.pantalla.blit(self.am.images["fire"], pos)
                else: pygame.draw.rect(self.pantalla, (255,100,0), (*pos, TAM_CELDA, TAM_CELDA))

        # 5. DIBUJAR ENEMIGOS (Aquí añadimos el Tanque)
        for e in estado.enemigos:
            if e.vivo:
                pos = (e.x*TAM_CELDA, e.y*TAM_CELDA)
                k = "enemy_smile"
                if e.tipo=="SMOKE": k="enemy_ghost"
                if e.tipo=="SLIME": k="enemy_hunter"
                
                # ### CAMBIO AQUI 2: Lógica para pintar el Tanque ###
                if e.tipo=="TANK": k="enemy_tank" # <--- NUEVO
                # -------------------------------------------------

                if self.am.images.get(k): self.pantalla.blit(self.am.images[k], pos)
                else: pygame.draw.circle(self.pantalla, (255,0,0), (pos[0]+25, pos[1]+25), 20)

        # 6. DIBUJAR JEFE
        if estado.jefe and estado.jefe.vivo:
            if self.am.images["boss"]: self.pantalla.blit(self.am.images["boss"], (estado.jefe.x, estado.jefe.y))
            else: pygame.draw.rect(self.pantalla, (255,0,255), (estado.jefe.x, estado.jefe.y, 150, 150))
            # Barra de vida del jefe
            pct = max(0, estado.jefe.vida/estado.jefe.max_vida)
            pygame.draw.rect(self.pantalla, (100,0,0), (200,20,400,20))
            pygame.draw.rect(self.pantalla, (255,0,0), (200,20,400*pct,20))
            pygame.draw.rect(self.pantalla, BLANCO, (200,20,400,20), 2)

        # 7. DIBUJAR JUGADORES
        for pid, p in estado.jugadores.items():
            if p.vivo:
                ox = (TAM_CELDA - 64)//2
                oy = (TAM_CELDA - 64) - 5
                pos = (p.x*TAM_CELDA+ox, p.y*TAM_CELDA+oy)
                sk = "player1" if p.color==AZUL_J1 else "player2"
                if self.am.images.get(sk): self.pantalla.blit(self.am.images[sk], pos)
                else: pygame.draw.rect(self.pantalla, p.color, (p.x*TAM_CELDA+10, p.y*TAM_CELDA+10, 30, 30))
                if p.escudo_activo:
                    pygame.draw.circle(self.pantalla, (255,255,255), (p.x*TAM_CELDA+25, p.y*TAM_CELDA+25), 25, 2)

        # HUD (Puntaje)
        if mi_id in estado.jugadores:
            txt = self.am.fonts["ui"].render(f"P: {estado.jugadores[mi_id].score} | NV: {estado.nivel_actual}", True, BLANCO)
            self.pantalla.blit(txt, (10, ALTO-30))

    def dibujar_pausa(self):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); s.fill((0,0,0,150))
        self.pantalla.blit(s,(0,0))
        txt = self.am.fonts["big"].render("PAUSA", True, BLANCO)
        self.pantalla.blit(txt, (ANCHO//2-txt.get_width()//2, ALTO//2-50))
        txt2 = self.am.fonts["ui"].render("P para Continuar - ESC para Menú", True, BLANCO)
        self.pantalla.blit(txt2, (ANCHO//2-txt2.get_width()//2, ALTO//2+20))

    def dibujar_nivel_completado(self, nivel):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); s.fill((0,0,0,200))
        self.pantalla.blit(s,(0,0))
        txt = self.am.fonts["big"].render(f"NIVEL {nivel} COMPLETADO", True, DORADO)
        self.pantalla.blit(txt, (ANCHO//2-txt.get_width()//2, ALTO//2-50))
        txt2 = self.am.fonts["ui"].render("Presiona ENTER para Siguiente Nivel", True, BLANCO)
        self.pantalla.blit(txt2, (ANCHO//2-txt2.get_width()//2, ALTO//2+50))

    def dibujar_victoria_trofeo(self):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); s.fill((0,0,0,200))
        self.pantalla.blit(s,(0,0))
        ren = self.am.fonts["big"].render("¡JUEGO COMPLETADO!", True, DORADO)
        self.pantalla.blit(ren, (ANCHO//2-ren.get_width()//2, 50))
        if self.am.images.get("trophy"):
            rect_trofeo = self.am.images["trophy"].get_rect(center=(ANCHO//2, ALTO//2))
            self.pantalla.blit(self.am.images["trophy"], rect_trofeo)
            txt = self.am.fonts["ui"].render("HAZ CLICK EN EL TROFEO", True, BLANCO)
            self.pantalla.blit(txt, (ANCHO//2 - txt.get_width()//2, rect_trofeo.bottom + 20))
            return rect_trofeo
        else:
            return pygame.Rect(0,0,0,0)

    def dibujar_mensaje_final(self, tipo, jugadores):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); s.fill((0,0,0,200))
        self.pantalla.blit(s,(0,0))
        txt = "VICTORIA" if tipo=="WIN" else "GAME OVER"
        c = DORADO if tipo=="WIN" else ROJO_J2
        ren = self.am.fonts["big"].render(txt, True, c)
        self.pantalla.blit(ren, (ANCHO//2-ren.get_width()//2, 150))
        y = 300
        for pid, p in jugadores.items():
            t = self.am.fonts["ui"].render(f"{pid}: {p.score} pts", True, p.color)
            self.pantalla.blit(t, (ANCHO//2-50, y)); y+=30
        t_cont = self.am.fonts["ui"].render("PRESIONA ENTER PARA CONTINUAR", True, BLANCO)
        self.pantalla.blit(t_cont, (ANCHO//2-t_cont.get_width()//2, 500))

    def dibujar_input_nombre(self, nombre_actual):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); s.fill((0,0,0,220))
        self.pantalla.blit(s, (0,0))
        t1 = self.am.fonts["big"].render("INGRESA TU NOMBRE", True, BLANCO)
        self.pantalla.blit(t1, (ANCHO//2 - t1.get_width()//2, 150))
        pygame.draw.rect(self.pantalla, AZUL_J1, (200, 300, 400, 60), 2)
        t2 = self.am.fonts["med"].render(nombre_actual + "_", True, AZUL_J1)
        self.pantalla.blit(t2, (ANCHO//2 - t2.get_width()//2, 310))
        t3 = self.am.fonts["ui"].render("ENTER para Guardar", True, BLANCO)
        self.pantalla.blit(t3, (ANCHO//2 - t3.get_width()//2, 400))

    def dibujar_tabla_puntajes(self, scores):
        s = pygame.Surface((ANCHO, ALTO)); s.fill(NEGRO)
        self.pantalla.blit(s, (0,0))
        if self.am.images.get("bg_score"):
            self.pantalla.blit(self.am.images["bg_score"], (0,0))
            dark = pygame.Surface((ANCHO, ALTO)); dark.set_alpha(150); dark.fill(NEGRO)
            self.pantalla.blit(dark, (0,0))
        tit = self.am.fonts["big"].render("TABLA DE PUNTUACIONES", True, DORADO)
        self.pantalla.blit(tit, (ANCHO//2 - tit.get_width()//2, 50))
        y = 150
        for i, sc in enumerate(scores):
            col = DORADO if i == 0 else BLANCO
            t = self.am.fonts["ui"].render(f"{i+1}. {sc['nombre']} - {sc['score']}", True, col)
            self.pantalla.blit(t, (ANCHO//2 - 100, y)); y += 35
        t_esc = self.am.fonts["ui"].render("ESC para Volver al Menú", True, ROJO_J2)
        self.pantalla.blit(t_esc, (ANCHO//2 - t_esc.get_width()//2, 550))