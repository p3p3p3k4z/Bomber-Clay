import random
from config import *

class MapGenerator:
    @staticmethod
    def generar(nivel):
        mapa = [[V for _ in range(COLS)] for _ in range(FILAS)]
        
        # 1. Bordes Fijos (Perímetro)
        for y in range(FILAS):
            for x in range(COLS):
                if x == 0 or x == COLS - 1 or y == 0 or y == FILAS - 1:
                    mapa[y][x] = R

        # Configuración de Densidad
        if nivel == 3: # Jefe (Arena más limpia)
            prob_muro = 0.15
            prob_arbusto = 0.20
        else:
            # Niveles normales
            # Aumentamos probabilidad de arbustos para el gameplay, pero pocos muros fijos
            prob_muro = 0.20 + (nivel * 0.02)
            prob_arbusto = 0.30 + (nivel * 0.05)

        # 2. Relleno Aleatorio (Sin patrón ajedrez)
        for y in range(1, FILAS - 1):
            for x in range(1, COLS - 1):
                # Zona Segura (Esquinas)
                d1 = x + y
                d2 = (COLS-1-x) + y
                d3 = x + (FILAS-1-y)
                d4 = (COLS-1-x) + (FILAS-1-y)
                
                # Radio de seguridad bloques para no encerrar
                if min(d1, d2, d3, d4) < 5:
                    mapa[y][x] = V
                    continue

                r = random.random()
                if r < prob_muro: mapa[y][x] = R
                elif r < prob_muro + prob_arbusto: mapa[y][x] = B
                else: mapa[y][x] = V
        return mapa