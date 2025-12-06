import math
import time
import os

# --- DIMENSIONES ---
ANCHO, ALTO = 800, 600
TAM_CELDA = 50
COLS = ANCHO // TAM_CELDA
FILAS = ALTO // TAM_CELDA
FPS = 60

# --- RED ---
PUERTO = 7777
BUFF_SIZE = 32768 

# --- ESTADOS DEL JUEGO ---
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
STATE_WIN = 3
STATE_SCOREBOARD = 4
STATE_INPUT_NAME = 5
STATE_NEXT_LEVEL = 6      # Transición técnica
STATE_LEVEL_COMPLETED = 7 # Pantalla visual de "Nivel Completado"
STATE_PAUSE = 8           # Menú de Pausa

# --- CÓDIGOS DE MATRIZ ---
V = 0  # Vacío
R = 1  # Roca (Indestructible)
B = 2  # Basura (Destructible)
# Items
ITEM_BOMBA = 6
ITEM_VELOCIDAD = 7
ITEM_ESCUDO = 8

# --- JEFE ---
BOSS_HP = 15

# --- COLORES ---
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
AZUL_J1 = (0, 255, 255)
ROJO_J2 = (255, 50, 100)
DORADO = (255, 215, 0)
COLOR_FONDO_DEFAULT = (20, 20, 40)