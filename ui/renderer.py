import pygame
import math
import time
import random
from config import *

class Renderer:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.font = pygame.font.SysFont("Consolas", 20)
        self.font_big = pygame.font.SysFont("Impact", 60)

    def dibujar_juego(self, estado, mi_id):
        self.pantalla.fill(COLOR_FONDO())
        t = time.time()

        # 1. MAPA
        for y in range(FILAS):
            for x in range(COLS):
                cell = estado.mapa[y][x]
                rect = (x * TAM_CELDA, y * TAM_CELDA, TAM_CELDA, TAM_CELDA)
                
                if cell == R:
                    pygame.draw.rect(self.pantalla, GRIS_PIEDRA, rect)
                    pygame.draw.rect(self.pantalla, (20,20,20), rect, 2)
                elif cell == B:
                    # Basura glitch
                    col = (random.randint(50, 150), 0, random.randint(100, 200))
                    pygame.draw.rect(self.pantalla, col, rect)
                    if random.random() < 0.05:
                        pygame.draw.line(self.pantalla, BLANCO, rect[:2], (rect[0]+40, rect[1]+40))

        # 2. BOMBAS
        for b in estado.bombas:
            cx, cy = b.x * TAM_CELDA + 25, b.y * TAM_CELDA + 25
            r = 15 + 5 * math.sin(t * 10)
            pygame.draw.circle(self.pantalla, BLANCO, (cx, cy), r)
            pygame.draw.circle(self.pantalla, (255, 0, 0), (cx, cy), 10)

        # 3. EXPLOSIONES
        for e in estado.explosiones:
            rgb = (int(127+127*math.sin(t*10)), int(127+127*math.sin(t*10+2)), int(127+127*math.sin(t*10+4)))
            for (ex, ey) in e.celdas:
                rect = (ex * TAM_CELDA, ey * TAM_CELDA, TAM_CELDA, TAM_CELDA)
                pygame.draw.rect(self.pantalla, rgb, rect)

        # 4. ENEMIGOS (Diferenciados)
        for e in estado.enemigos:
            if e.vivo:
                self.dibujar_enemigo(e.x, e.y, e.tipo, t)

        # 5. JUGADORES
        jugador_vivo = False
        for pid, p in estado.jugadores.items():
            if p.vivo:
                if pid == mi_id: jugador_vivo = True
                rect = (p.x * TAM_CELDA + 10, p.y * TAM_CELDA + 10, 30, 30)
                pygame.draw.rect(self.pantalla, p.color, rect, border_radius=5)
                if pid == mi_id:
                    pygame.draw.rect(self.pantalla, BLANCO, rect, 2, border_radius=5)
        
        # Game Over HUD
        if not jugador_vivo and mi_id in estado.jugadores:
            txt = self.font_big.render("ELIMINADO", True, (255, 0, 0))
            self.pantalla.blit(txt, (ANCHO//2 - 100, ALTO//2 - 30))

    def dibujar_enemigo(self, x, y, tipo, t):
        cx, cy = x * TAM_CELDA + 25, y * TAM_CELDA + 25
        
        if tipo == "SMILE":
            # Amarillo, rebota
            pygame.draw.circle(self.pantalla, (255, 255, 0), (cx, cy), 20)
            off_x = 5 * math.cos(t*5)
            pygame.draw.circle(self.pantalla, NEGRO, (cx-7+off_x, cy-5), 3)
            pygame.draw.circle(self.pantalla, NEGRO, (cx+7+off_x, cy-5), 3)
            pygame.draw.arc(self.pantalla, NEGRO, (cx-10, cy-5, 20, 15), 3.14, 6.28, 2)
            
        elif tipo == "SLIME": # Cazador
            # Verde agresivo, palpita rápido
            h = 18 + 5 * math.sin(t*15) 
            # Ojos rojos de cazador
            pygame.draw.ellipse(self.pantalla, (0, 255, 50), (cx-20, cy-h, 40, h*2))
            pygame.draw.circle(self.pantalla, (255, 0, 0), (cx-8, cy-5), 4)
            pygame.draw.circle(self.pantalla, (255, 0, 0), (cx+8, cy-5), 4)
            
        elif tipo == "SMOKE": # Fantasma
            # Gris translúcido
            for i in range(3):
                ox = 10 * math.cos(t*2 + i)
                oy = 10 * math.sin(t*3 + i)
                s = pygame.Surface((30,30), pygame.SRCALPHA)
                # Alfa bajo para efecto fantasma
                pygame.draw.circle(s, (200, 200, 255, 80), (15,15), 10) 
                self.pantalla.blit(s, (cx+ox-15, cy+oy-15))