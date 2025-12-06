import pygame
import os
from config import *

class AssetManager:
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.fonts = {}
        
        # Inicializar fuentes
        self.fonts["ui"] = pygame.font.SysFont("Consolas", 20, bold=True)
        self.fonts["big"] = pygame.font.SysFont("Impact", 60)
        self.fonts["med"] = pygame.font.SysFont("Impact", 40)

        self.cargar_imagenes()
        self.cargar_sonidos()

    def cargar_imagenes(self):
        lista = {
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
            "bg_score": "assets/intro_bg.png",
            "item_bomb": "assets/item_bomb.png",
            "item_speed": "assets/item_speed.png",
            "item_shield": "assets/item_shield.png",
            "trophy": "assets/trophy.png"
        }

        for key, path in lista.items():
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Escalado
                    if "bg_" in key or "intro" in key:
                        self.images[key] = pygame.transform.scale(img, (ANCHO, ALTO))
                    elif key in ["player1", "player2"]:
                        self.images[key] = pygame.transform.scale(img, (64, 64))
                    elif key == "boss":
                        self.images[key] = pygame.transform.scale(img, (150, 150))
                    elif key == "trophy":
                        self.images[key] = pygame.transform.scale(img, (200, 200))
                    else:
                        self.images[key] = pygame.transform.scale(img, (TAM_CELDA, TAM_CELDA))
                except: self.images[key] = None
            else: self.images[key] = None

    def cargar_sonidos(self):
        fx = {
            "EXPLOSION": "assets/explosion.mp3",
            "ENEMY_DIE": "assets/hit.wav",
            "DEATH_PLAYER": "assets/hit.wav",
            "BOSS_HIT": "assets/hit.wav",
            "BOSS_DIE": "assets/hit.wav",
            "POWERUP": "assets/powerup.wav", 
            "LEVEL_UP": "assets/powerup.wav" 
        }
        for k, p in fx.items():
            if os.path.exists(p):
                try: self.sounds[k] = pygame.mixer.Sound(p)
                except: pass
        
        if "EXPLOSION" in self.sounds: self.sounds["EXPLOSION"].set_volume(0.5)

    def reproducir_sonido(self, nombre):
        if nombre in self.sounds:
            self.sounds[nombre].play()

    def reproducir_musica(self, nivel_o_tipo):
        pygame.mixer.music.stop()
        path = None
        
        if nivel_o_tipo == "INTRO": path = "assets/intro.mp3"
        elif nivel_o_tipo == "RANKING": 
            path = "assets/ranking.mp3"
        elif nivel_o_tipo == 3: path = "assets/music_boss.mp3"
        
        else:
            opciones = ["assets/musica.mp3", "assets/music_1.mp3", "assets/music_2.mp3","assets/music_3.mp3","assets/music_4.mp3"]
            disponibles = [p for p in opciones if os.path.exists(p)]
            if disponibles: 
                import random
                path = random.choice(disponibles)
        
        if path and os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play(-1)
            except: pass