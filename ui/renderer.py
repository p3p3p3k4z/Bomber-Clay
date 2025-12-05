import pygame
import math
import time
import random
import os
from config import *

class Renderer:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.font = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_big = pygame.font.SysFont("Impact", 80)
        
        # --- CARGADOR INTELIGENTE DE ASSETS ---
        self.assets = {}
        self.cargar_assets()
        
    def cargar_assets(self):
        """Carga imágenes específicas. Si falla alguna, usa None."""
        nombres = {
            # Entorno
            "wall": "assets/wall.png",
            "bush": "assets/bush.png",
            "bomb": "assets/bomb.png",
            "fondo": "assets/fondo.png",
            
            # Jugadores (Diferentes skins)
            "player1": "assets/player1.png", # Azul/Host
            "player2": "assets/player2.png", # Rojo/Cliente
            
            # Enemigos (Variedad)
            "enemy_smile": "assets/enemy_smile.png",   # Errático
            "enemy_ghost": "assets/enemy_ghost.png",   # Fantasma (Smoke)
            "enemy_hunter": "assets/enemy_hunter.png", # Cazador (Slime)
            
            # Items (Power-ups)
            "item_bomb": "assets/item_bomb.png",
            "item_speed": "assets/item_speed.png",
            "item_shield": "assets/item_shield.png"
        }
        
        for key, path in nombres.items():
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Escalar todo a TAM_CELDA (32x32 o 50x50 según config)
                    if key == "fondo":
                        self.assets[key] = pygame.transform.scale(img, (ANCHO, ALTO))
                    else:
                        self.assets[key] = pygame.transform.scale(img, (TAM_CELDA, TAM_CELDA))
                    print(f"[ASSET] Cargado: {path}")
                except Exception as e:
                    print(f"[ERROR] No se pudo cargar {path}: {e}")
                    self.assets[key] = None
            else:
                self.assets[key] = None

    def dibujar_juego(self, estado, mi_id):
        # 1. FONDO
        if self.assets["fondo"]:
            self.pantalla.blit(self.assets["fondo"], (0,0))
            # Oscurecer un poco el fondo para contraste
            s = pygame.Surface((ANCHO,ALTO)); s.set_alpha(80); s.fill(NEGRO)
            self.pantalla.blit(s, (0,0))
        else:
            self.pantalla.fill(COLOR_FONDO())

        t = time.time()

        # 2. MAPA E ITEMS
        for y in range(FILAS):
            for x in range(COLS):
                cell = estado.mapa[y][x]
                rect = (x * TAM_CELDA, y * TAM_CELDA)
                
                # ROCA (Muro Fijo)
                if cell == R:
                    if self.assets["wall"]:
                        self.pantalla.blit(self.assets["wall"], rect)
                    else:
                        pygame.draw.rect(self.pantalla, GRIS_PIEDRA, (*rect, TAM_CELDA, TAM_CELDA))
                        pygame.draw.rect(self.pantalla, NEGRO, (*rect, TAM_CELDA, TAM_CELDA), 2)
                
                # BASURA (Destructible)
                elif cell == B:
                    if self.assets["bush"]:
                        self.pantalla.blit(self.assets["bush"], rect)
                    else:
                        pygame.draw.rect(self.pantalla, (0, 100, 0), (*rect, TAM_CELDA, TAM_CELDA))
                        pygame.draw.line(self.pantalla, BLANCO, rect, (rect[0]+TAM_CELDA, rect[1]+TAM_CELDA))
                
                # ITEMS (Con sprites específicos)
                elif cell == ITEM_BOMBA:
                    self.dibujar_sprite_o_neon("item_bomb", rect, (255, 50, 50))
                elif cell == ITEM_VELOCIDAD:
                    self.dibujar_sprite_o_neon("item_speed", rect, (0, 255, 255))
                elif cell == ITEM_ESCUDO:
                    self.dibujar_sprite_o_neon("item_shield", rect, (255, 255, 0))

        # 3. BOMBAS
        for b in estado.bombas:
            pos = (b.x * TAM_CELDA, b.y * TAM_CELDA)
            if self.assets["bomb"]:
                # Efecto de palpitación
                scale = 1.0 + 0.1 * math.sin(t*10)
                w = int(TAM_CELDA*scale)
                img = pygame.transform.scale(self.assets["bomb"], (w, w))
                offset = (TAM_CELDA - img.get_width()) // 2
                self.pantalla.blit(img, (pos[0]+offset, pos[1]+offset))
            else:
                cx, cy = pos[0] + TAM_CELDA//2, pos[1] + TAM_CELDA//2
                pygame.draw.circle(self.pantalla, BLANCO, (cx, cy), TAM_CELDA//3)
                pygame.draw.circle(self.pantalla, (255, 0, 0), (cx, cy), TAM_CELDA//4)

        # 4. EXPLOSIONES (Neon siempre se ve mejor para el fuego mágico)
        for e in estado.explosiones:
            color = (int(127+127*math.sin(t*10)), 100, 0)
            for (ex, ey) in e.celdas:
                r = (ex * TAM_CELDA, ey * TAM_CELDA, TAM_CELDA, TAM_CELDA)
                pygame.draw.rect(self.pantalla, color, r)
                pygame.draw.rect(self.pantalla, (255, 200, 0), r, 4)

        # 5. ENEMIGOS (Diferenciados por Tipo)
        for e in estado.enemigos:
            if e.vivo:
                rect = (e.x * TAM_CELDA, e.y * TAM_CELDA)
                
                # Mapeo de tipo de enemigo a nombre de asset
                asset_key = "enemy_smile" # Default
                if e.tipo == "SMOKE": asset_key = "enemy_ghost"
                elif e.tipo == "SLIME": asset_key = "enemy_hunter"

                if self.assets[asset_key]:
                    # Pequeño rebote vertical
                    offset_y = int(5 * math.sin(t*10))
                    self.pantalla.blit(self.assets[asset_key], (rect[0], rect[1] + offset_y))
                else:
                    # Fallback neon si no hay imagen específica
                    self.dibujar_entidad_neon(e.x, e.y, e.tipo, t, False)

        # 6. JUGADORES (Diferenciados por Color/Rol)
        for pid, p in estado.jugadores.items():
            if p.vivo:
                rect = (p.x * TAM_CELDA, p.y * TAM_CELDA)
                
                # Determinar skin basado en color (Host es Azul, Cliente es Rojo usualmente)
                skin = "player1" if p.color == AZUL_J1 else "player2"
                
                if self.assets[skin]:
                    self.pantalla.blit(self.assets[skin], rect)
                else:
                    self.dibujar_entidad_neon(p.x, p.y, p.color, t, True)
                
                # Escudo visual (Overlay)
                if p.escudo_activo:
                    cx, cy = rect[0] + TAM_CELDA//2, rect[1] + TAM_CELDA//2
                    pygame.draw.circle(self.pantalla, (255, 255, 255), (cx, cy), TAM_CELDA//2, 2)

        # 7. HUD
        if mi_id in estado.jugadores:
            yo = estado.jugadores[mi_id]
            bg = pygame.Surface((200, 30)); bg.set_alpha(150); bg.fill(NEGRO)
            self.pantalla.blit(bg, (0,0))
            txt = self.font.render(f"SCORE: {yo.score}", True, BLANCO)
            self.pantalla.blit(txt, (10, 5))

    def dibujar_sprite_o_neon(self, asset_key, rect, color_neon):
        """Helper para dibujar items"""
        if self.assets[asset_key]:
            self.pantalla.blit(self.assets[asset_key], rect)
        else:
            cx, cy = rect[0] + TAM_CELDA//2, rect[1] + TAM_CELDA//2
            pygame.draw.circle(self.pantalla, NEGRO, (cx, cy), 16)
            pygame.draw.circle(self.pantalla, color_neon, (cx, cy), 12)
            pygame.draw.circle(self.pantalla, BLANCO, (cx, cy), 12, 1)

    def dibujar_entidad_neon(self, x, y, tipo, t, is_player):
        cx, cy = x * TAM_CELDA + 25, y * TAM_CELDA + 25
        if is_player:
            # Tipo aquí es el color (tupla)
            pygame.draw.rect(self.pantalla, tipo, (cx-15, cy-15, 30, 30), border_radius=5)
            pygame.draw.rect(self.pantalla, BLANCO, (cx-10, cy-8, 8, 8))
            pygame.draw.rect(self.pantalla, BLANCO, (cx+2, cy-8, 8, 8))
        else:
            # Fallback para enemigos si no hay imagen
            if tipo == "SMILE": pygame.draw.circle(self.pantalla, (255, 255, 0), (cx, cy), 18)
            elif tipo == "SLIME": pygame.draw.ellipse(self.pantalla, (0, 255, 50), (cx-15, cy-20, 30, 40))
            elif tipo == "SMOKE": pygame.draw.circle(self.pantalla, (200, 200, 255), (cx, cy), 15, 2)

    def dibujar_mensaje_final(self, estado_partida, jugadores):
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.pantalla.blit(s, (0,0))
        
        texto = "VICTORIA" if estado_partida == "WIN" else "GAME OVER"
        col = DORADO if estado_partida == "WIN" else ROJO_J2
        
        titulo = self.font_big.render(texto, True, col)
        self.pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 150))
        
        y = 300
        for pid, p in jugadores.items():
            txt = f"JUGADOR {pid}: {p.score} pts"
            ren = self.font.render(txt, True, p.color)
            self.pantalla.blit(ren, (ANCHO//2 - 100, y))
            y += 30
            
        exit_txt = self.font.render("Presiona ESC para salir", True, (150, 150, 150))
        self.pantalla.blit(exit_txt, (ANCHO//2 - 120, 500))