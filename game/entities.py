import time
import random
import math
from config import *

# --- JUGADOR Y BOMBAS (Sin cambios mayores) ---
class Jugador:
    def __init__(self, id, x, y, color):
        self.id = id
        self.x = x
        self.y = y
        self.color = color
        self.vivo = True
        self.bombas_disponibles = 1

class Bomba:
    def __init__(self, x, y, owner_id):
        self.x = x
        self.y = y
        self.owner_id = owner_id
        self.tiempo_detonacion = time.time() + 3.0
        self.radio = 2

class Explosion:
    def __init__(self, celdas):
        self.celdas = celdas
        self.tiempo_fin = time.time() + 0.5

# --- JERARQUÍA DE ENEMIGOS ---

class Enemigo:
    """Clase Padre: Define lo básico que tiene cualquier monstruo"""
    def __init__(self, x, y, tipo):
        self.x = x
        self.y = y
        self.tipo = tipo
        self.vivo = True
        self.timer_mov = 0
        self.velocidad = 1.0 # Segundos entre movimientos (Menor es más rápido)

    def puede_moverse(self, nx, ny, mapa):
        # Por defecto, solo caminan en vacío
        if 0 <= nx < COLS and 0 <= ny < FILAS:
            return mapa[ny][nx] == V
        return False

    def mover(self, mapa, jugadores):
        """Método vacío para ser sobrescrito por los hijos"""
        pass

class EnemigoErratico(Enemigo):
    """(SMILE) Se mueve completamente al azar"""
    def __init__(self, x, y):
        super().__init__(x, y, "SMILE")
        self.velocidad = 0.8

    def mover(self, mapa, jugadores):
        if time.time() > self.timer_mov:
            dirs = [(0,1), (0,-1), (1,0), (-1,0)]
            random.shuffle(dirs)
            
            for dx, dy in dirs:
                nx, ny = self.x + dx, self.y + dy
                if self.puede_moverse(nx, ny, mapa):
                    self.x, self.y = nx, ny
                    break
            
            self.timer_mov = time.time() + self.velocidad

class EnemigoFantasma(Enemigo):
    """(SMOKE) Atraviesa la basura y muros blandos"""
    def __init__(self, x, y):
        super().__init__(x, y, "SMOKE")
        self.velocidad = 1.2 # Es lento pero atraviesa paredes

    def puede_moverse(self, nx, ny, mapa):
        # Sobrescribimos: Puede caminar en VACÍO (V) y BASURA (B)
        if 0 <= nx < COLS and 0 <= ny < FILAS:
            return mapa[ny][nx] in [V, B]
        return False

    def mover(self, mapa, jugadores):
        # Movimiento aleatorio pero con la capacidad de atravesar
        if time.time() > self.timer_mov:
            dirs = [(0,1), (0,-1), (1,0), (-1,0)]
            dx, dy = random.choice(dirs)
            nx, ny = self.x + dx, self.y + dy
            
            if self.puede_moverse(nx, ny, mapa):
                self.x, self.y = nx, ny
            
            self.timer_mov = time.time() + self.velocidad

class EnemigoCazador(Enemigo):
    """(SLIME) Persigue al jugador más cercano"""
    def __init__(self, x, y):
        super().__init__(x, y, "SLIME")
        self.velocidad = 0.6 # Es rápido

    def mover(self, mapa, jugadores):
        if time.time() > self.timer_mov:
            target = None
            min_dist = 999
            
            # 1. Buscar jugador más cercano
            for p in jugadores.values():
                if p.vivo:
                    dist = abs(p.x - self.x) + abs(p.y - self.y)
                    if dist < min_dist and dist < 8: # Radio de visión de 8 bloques
                        min_dist = dist
                        target = p

            # 2. Decidir dirección
            if target:
                # IA Básica: Intentar acercarse en X, luego en Y
                dx = 1 if target.x > self.x else -1 if target.x < self.x else 0
                dy = 1 if target.y > self.y else -1 if target.y < self.y else 0
                
                movimientos_posibles = []
                if dx != 0: movimientos_posibles.append((dx, 0))
                if dy != 0: movimientos_posibles.append((0, dy))
                
                # Si no hay camino directo, probar aleatorio para desatascarse
                if not movimientos_posibles:
                     movimientos_posibles = [(0,1), (0,-1), (1,0), (-1,0)]

                moved = False
                for mx, my in movimientos_posibles:
                    nx, ny = self.x + mx, self.y + my
                    if self.puede_moverse(nx, ny, mapa):
                        self.x, self.y = nx, ny
                        moved = True
                        break
                
                # Si está bloqueado intentando perseguir, moverse al azar
                if not moved:
                    dirs = [(0,1), (0,-1), (1,0), (-1,0)]
                    dx, dy = random.choice(dirs)
                    nx, ny = self.x + dx, self.y + dy
                    if self.puede_moverse(nx, ny, mapa): self.x, self.y = nx, ny

            else:
                # Si no ve a nadie, patrulla al azar
                dirs = [(0,1), (0,-1), (1,0), (-1,0)]
                dx, dy = random.choice(dirs)
                nx, ny = self.x + dx, self.y + dy
                if self.puede_moverse(nx, ny, mapa): self.x, self.y = nx, ny

            self.timer_mov = time.time() + self.velocidad