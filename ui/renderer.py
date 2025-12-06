import pygame
import math
import time
import os
from config import *

class Renderer:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.font = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_big = pygame.font.SysFont("Impact", 60)
        self.assets = {}
        self.cargar_assets()

    def cargar_assets(self):
        nombres = {
            "player1": "assets/player1.png",
            "player2": "assets/player2.png",
            "wall": "assets/wall.png",
            "bush": "assets/bush.png",
            "enemy_smile": "assets/enemy_smile.png",
            "enemy_ghost": "assets/enemy_ghost.png",
            "enemy_hunter": "assets/enemy_hunter.png",
            "bomb": "assets/bomb.png",
            "fire": "assets/fire.png", 
            "boss": "assets/boss.png",
            "intro_bg": "assets/intro_bg.png",
            "bg_level1": "assets/bg_level1.png",
            "bg_level2": "assets/bg_level2.png",
            "bg_boss": "assets/bg_boss.png",
            "item_bomb": "assets/item_bomb.png",
            "item_speed": "assets/item_speed.png",
            "item_shield": "assets/item_shield.png"
        }
        for k, p in nombres.items():
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert_alpha()
                    if "bg_" in k or "intro" in k: self.assets[k] = pygame.transform.scale(img, (ANCHO, ALTO))
                    elif k in ["player1","player2"]: self.assets[k] = pygame.transform.scale(img, (64, 64))
                    elif k == "boss": self.assets[k] = pygame.transform.scale(img, (150, 150))
                    else: self.assets[k] = pygame.transform.scale(img, (TAM_CELDA, TAM_CELDA))
                except: self.assets[k] = None
            else: self.assets[k] = None

    def dibujar_boton(self, texto, x, y, w, h, hover=False):
        """
        Botón estilo Plastilina / Cristal Limpio.
        Eliminado el brillo blanco superior para mejorar legibilidad del texto.
        """
        # Colores
        color_base = (0, 180, 0) if not hover else (50, 230, 50)
        color_sombra = (0, 80, 0)
        color_borde_luz = (100, 255, 100) # Borde sutil en lugar de bloque blanco
        
        # 1. Sombra inferior (Profundidad)
        pygame.draw.rect(self.pantalla, color_sombra, (x, y+6, w, h), border_radius=12)
        
        # 2. Cuerpo Principal
        pygame.draw.rect(self.pantalla, color_base, (x, y, w, h), border_radius=12)
        
        # 3. Efecto Cristal (Sutil borde interno superior)
        # En lugar de un rectángulo blanco solido, dibujamos un borde delgado
        pygame.draw.rect(self.pantalla, color_borde_luz, (x+2, y+2, w-4, h-4), 2, border_radius=10)
        
        # 4. Texto Centrado
        txt = self.font.render(texto, True, BLANCO)
        self.pantalla.blit(txt, (x + (w - txt.get_width())//2, y + (h - txt.get_height())//2))

    def dibujar_juego(self, estado, mi_id):
        # Fondo Nivel
        bg = "bg_level1"
        if estado.nivel_actual == 2: bg = "bg_level2"
        if estado.nivel_actual == 3: bg = "bg_boss"
        
        if self.assets.get(bg):
            self.pantalla.blit(self.assets[bg], (0,0))
            s=pygame.Surface((ANCHO,ALTO)); s.set_alpha(60); s.fill(NEGRO)
            self.pantalla.blit(s,(0,0))
        else: self.pantalla.fill(COLOR_FONDO_DEFAULT)

        t = time.time()

        # Mapa
        for y in range(FILAS):
            for x in range(COLS):
                c = estado.mapa[y][x]
                r = (x*TAM_CELDA, y*TAM_CELDA)
                if c==R:
                    if self.assets["wall"]: self.pantalla.blit(self.assets["wall"], r)
                    else: pygame.draw.rect(self.pantalla, (100,100,100), (*r, TAM_CELDA, TAM_CELDA))
                elif c==B:
                    if self.assets["bush"]: self.pantalla.blit(self.assets["bush"], r)
                    else: pygame.draw.rect(self.pantalla, (0,100,0), (*r, TAM_CELDA, TAM_CELDA))
                elif c>=ITEM_BOMBA:
                    k = "item_bomb" if c==ITEM_BOMBA else "item_speed" if c==ITEM_VELOCIDAD else "item_shield"
                    if self.assets[k]: self.pantalla.blit(self.assets[k], r)
                    else: pygame.draw.circle(self.pantalla, (255,255,0), (r[0]+25,r[1]+25), 10)

        # Bombas
        for b in estado.bombas:
            pos = (b.x*TAM_CELDA, b.y*TAM_CELDA)
            if self.assets["bomb"]:
                sc = 1.0 + 0.05*math.sin(t*15)
                img = pygame.transform.scale(self.assets["bomb"], (int(TAM_CELDA*sc), int(TAM_CELDA*sc)))
                self.pantalla.blit(img, (pos[0]+(TAM_CELDA-img.get_width())//2, pos[1]))
            else: pygame.draw.circle(self.pantalla, BLANCO, (pos[0]+25, pos[1]+25), 20)

        # Explosiones
        for e in estado.explosiones:
            for (ex,ey) in e.celdas:
                pos = (ex*TAM_CELDA, ey*TAM_CELDA)
                if self.assets["fire"]: self.pantalla.blit(self.assets["fire"], pos)
                else: pygame.draw.rect(self.pantalla, (255,100,0), (*pos, TAM_CELDA, TAM_CELDA))

        # Enemigos
        for e in estado.enemigos:
            if e.vivo:
                pos = (e.x*TAM_CELDA, e.y*TAM_CELDA)
                k = "enemy_smile"
                if e.tipo=="SMOKE": k="enemy_ghost"
                if e.tipo=="SLIME": k="enemy_hunter"
                if self.assets[k]:
                    oy = int(5*math.sin(t*10))
                    self.pantalla.blit(self.assets[k], (pos[0], pos[1]+oy))
                else: pygame.draw.circle(self.pantalla, (255,0,0), (pos[0]+25, pos[1]+25), 20)

        # Jefe
        if estado.jefe and estado.jefe.vivo:
            if self.assets["boss"]: self.pantalla.blit(self.assets["boss"], (estado.jefe.x, estado.jefe.y))
            else: pygame.draw.rect(self.pantalla, (255,0,255), (estado.jefe.x, estado.jefe.y, 150, 150))
            # Barra HP
            pct = max(0, estado.jefe.vida/estado.jefe.max_vida)
            pygame.draw.rect(self.pantalla, (100,0,0), (200,20,400,20))
            pygame.draw.rect(self.pantalla, (255,0,0), (200,20,400*pct,20))
            pygame.draw.rect(self.pantalla, BLANCO, (200,20,400,20), 2)

        # Jugadores
        for pid, p in estado.jugadores.items():
            if p.vivo:
                # Centrar 64x64
                ox = (TAM_CELDA - 64)//2
                oy = (TAM_CELDA - 64) - 5
                pos = (p.x*TAM_CELDA+ox, p.y*TAM_CELDA+oy)
                sk = "player1" if p.color==AZUL_J1 else "player2"
                if self.assets[sk]: self.pantalla.blit(self.assets[sk], pos)
                else: pygame.draw.rect(self.pantalla, p.color, (p.x*TAM_CELDA+10, p.y*TAM_CELDA+10, 30, 30))
                if p.escudo_activo:
                    pygame.draw.circle(self.pantalla, (255,255,255), (p.x*TAM_CELDA+25, p.y*TAM_CELDA+25), 25, 2)

        # HUD
        if mi_id in estado.jugadores:
            txt = self.font.render(f"P: {estado.jugadores[mi_id].score} | NV: {estado.nivel_actual}", True, BLANCO)
            self.pantalla.blit(txt, (10, ALTO-30))

    def dibujar_mensaje_final(self, tipo, jugadores):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA); s.fill((0,0,0,200))
        self.pantalla.blit(s,(0,0))
        txt = "VICTORIA" if tipo=="WIN" else "GAME OVER"
        c = DORADO if tipo=="WIN" else ROJO_J2
        ren = self.font_big.render(txt, True, c)
        self.pantalla.blit(ren, (ANCHO//2-ren.get_width()//2, 150))
        y = 300
        for pid, p in jugadores.items():
            t = self.font.render(f"{pid}: {p.score} pts", True, p.color)
            self.pantalla.blit(t, (ANCHO//2-50, y)); y+=30