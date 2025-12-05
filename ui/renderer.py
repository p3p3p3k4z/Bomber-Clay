import pygame
import math
import time
import random
from config import *

class Renderer:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.font = pygame.font.SysFont("Consolas", 20)

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
                    # Basura que glitchea
                    col = (random.randint(50, 150), 0, random.randint(100, 200))
                    pygame.draw.rect(self.pantalla, col, rect)
                    if random.random() < 0.05:
                        pygame.draw.line(self.pantalla, BLANCO, rect[:2], (rect[0]+40, rect[1]+40))

        # 2. BOMBAS (Palpitan)
        for b in estado.bombas:
            cx, cy = b.x * TAM_CELDA + 25, b.y * TAM_CELDA + 25
            r = 15 + 5 * math.sin(t * 10)
            pygame.draw.circle(self.pantalla, BLANCO, (cx, cy), r)
            pygame.draw.circle(self.pantalla, (255, 0, 0), (cx, cy), 10)

        # 3. EXPLOSIONES (Neon Roots)
        for e in estado.explosiones:
            # Ciclo de colores arcoiris
            rgb = (int(127+127*math.sin(t*10)), int(127+127*math.sin(t*10+2)), int(127+127*math.sin(t*10+4)))
            for (ex, ey) in e.celdas:
                rect = (ex * TAM_CELDA, ey * TAM_CELDA, TAM_CELDA, TAM_CELDA)
                pygame.draw.rect(self.pantalla, rgb, rect)

        # 4. ENEMIGOS (Formas retorcidas)
        for e in estado.enemigos:
            if e.vivo:
                self.dibujar_enemigo(e.x, e.y, e.tipo, t)

        # 5. JUGADORES
        for pid, p in estado.jugadores.items():
            if p.vivo:
                rect = (p.x * TAM_CELDA + 10, p.y * TAM_CELDA + 10, 30, 30)
                pygame.draw.rect(self.pantalla, p.color, rect, border_radius=5)
                # Indicador "YO"
                if pid == mi_id:
                    pygame.draw.rect(self.pantalla, BLANCO, rect, 2, border_radius=5)

    def dibujar_enemigo(self, x, y, tipo, t):
        cx, cy = x * TAM_CELDA + 25, y * TAM_CELDA + 25
        
        if tipo == "SMILE":
            pygame.draw.circle(self.pantalla, (255, 255, 0), (cx, cy), 20)
            # Cara que rota
            off_x = 5 * math.cos(t*5)
            pygame.draw.circle(self.pantalla, NEGRO, (cx-7+off_x, cy-5), 3)
            pygame.draw.circle(self.pantalla, NEGRO, (cx+7+off_x, cy-5), 3)
            pygame.draw.arc(self.pantalla, NEGRO, (cx-10, cy-5, 20, 15), 3.14, 6.28, 2)
            
        elif tipo == "SLIME":
            h = 15 + 5 * math.sin(t*8)
            pygame.draw.ellipse(self.pantalla, (0, 255, 50), (cx-20, cy-h, 40, h*2))
            
        elif tipo == "SMOKE":
            for i in range(3):
                ox = 10 * math.cos(t*2 + i)
                oy = 10 * math.sin(t*3 + i)
                s = pygame.Surface((30,30), pygame.SRCALPHA)
                pygame.draw.circle(s, (150,150,150,100), (15,15), 10)
                self.pantalla.blit(s, (cx+ox-15, cy+oy-15))