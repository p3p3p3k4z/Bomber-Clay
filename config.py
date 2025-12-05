import math
import time

# --- DIMENSIONES ---
ANCHO, ALTO = 800, 600
TAM_CELDA = 50
COLS = ANCHO // TAM_CELDA
FILAS = ALTO // TAM_CELDA
FPS = 60

# --- RED ---
PUERTO = 7777
BUFF_SIZE = 16384

# --- COLORES DINÁMICOS ---
def COLOR_FONDO():
    t = time.time()
    return (int(10 + 5 * math.sin(t)), int(5 + 5 * math.cos(t)), 25)

NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS_PIEDRA = (40, 40, 40)
AZUL_J1 = (0, 255, 255)
ROJO_J2 = (255, 50, 100)
DORADO = (255, 215, 0) # Para victoria

# --- CÓDIGOS DE MATRIZ ---
V = 0  # Vacío
R = 1  # Roca
B = 2  # Basura
# 3-5 Reservados
ITEM_BOMBA = 6   # Power-up: Más bombas
ITEM_VELOCIDAD = 7 # Power-up: Patines
ITEM_ESCUDO = 8 # Power-up: Invulnerabilidad

# --- PUNTAJES ---
PUNTOS_BASURA = 10
PUNTOS_ENEMIGO = 100
PUNTOS_VICTORIA = 500