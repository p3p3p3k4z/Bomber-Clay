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
BUFF_SIZE = 16384  # Buffer grande para objetos serializados

# --- COLORES PSICODÉLICOS (Funciones Lambda) ---
def COLOR_FONDO():
    t = time.time()
    # Un fondo oscuro que "respira" levemente en morado/azul
    return (int(10 + 5 * math.sin(t)), int(5 + 5 * math.cos(t)), int(20 + 5 * math.sin(t*0.5)))

def COLOR_NEON_VERDE():
    t = time.time() * 5
    val = int(150 + 105 * math.sin(t))
    return (50, val, 100)

NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS_PIEDRA = (40, 40, 40)
MORADO_TOXICO = (100, 0, 150)
AZUL_J1 = (0, 255, 255)  # Cyan Neon
ROJO_J2 = (255, 50, 100) # Rosa Neon

# --- CÓDIGOS DE MATRIZ ---
V = 0  # Vacío
R = 1  # Roca (Indestructible)
B = 2  # Basura (Destructible)
# 3 = Bomba, 4 = Explosión