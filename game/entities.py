import time
import random
from config import *

# --- JUGADOR CON ÍTEMS Y PUNTAJE ---
class Jugador:
    def __init__(self, id, x, y, color):
        self.id = id
        self.x = x
        self.y = y
        self.color = color
        self.vivo = True
        
        # Estadísticas Nuevas (Requisitos nuevos)
        self.score = 0
        self.bombas_disponibles = 1
        self.max_bombas = 1
        self.velocidad_extra = False
        self.escudo_activo = False
        self.timer_efecto = 0 # Tiempo fin del efecto

    def aplicar_item(self, tipo):
        """Lógica para los Power-Ups"""
        if tipo == "BOMBA":
            self.max_bombas += 1
            self.bombas_disponibles += 1
        elif tipo == "VELOCIDAD":
            self.velocidad_extra = True
            self.timer_efecto = time.time() + 10 # Dura 10 segs
        elif tipo == "ESCUDO":
            self.escudo_activo = True
            self.timer_efecto = time.time() + 8 # Dura 8 segs

    def update(self):
        """Revisar si se acabaron los efectos temporales"""
        if time.time() > self.timer_efecto:
            self.velocidad_extra = False
            self.escudo_activo = False

# --- BOMBAS Y EXPLOSIONES ---
class Bomba:
    def __init__(self, x, y, owner_id):
        self.x = x
        self.y = y
        self.owner_id = owner_id
        self.tiempo_detonacion = time.time() + 3.0
        self.radio = 2 # Radio base

class Explosion:
    def __init__(self, celdas, owner_id):
        self.celdas = celdas
        self.owner_id = owner_id # Importante para sumar puntos al dueño
        self.tiempo_fin = time.time() + 0.5

# --- JERARQUÍA DE ENEMIGOS (FUSIONADA) ---

class Enemigo:
    """Clase Padre: Define lo básico"""
    def __init__(self, x, y, tipo):
        self.x = x
        self.y = y
        self.tipo = tipo # "SMILE", "SMOKE", "SLIME"
        self.vivo = True
        self.timer_mov = 0
        self.velocidad = 1.0 

    def get_velocidad(self):
        """Soluciona el AttributeError devolviendo la velocidad interna"""
        return self.velocidad

    def puede_moverse(self, nx, ny, mapa):
        # Por defecto, solo caminan en vacío
        if 0 <= nx < COLS and 0 <= ny < FILAS:
            return mapa[ny][nx] == V
        return False

    def mover(self, mapa, jugadores):
        pass

class EnemigoErratico(Enemigo):
    """(SMILE) Se mueve al azar"""
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
    """(SMOKE) Atraviesa basura"""
    def __init__(self, x, y):
        super().__init__(x, y, "SMOKE")
        self.velocidad = 1.2 # Lento pero atraviesa

    def puede_moverse(self, nx, ny, mapa):
        # Puede caminar en VACÍO (V) y BASURA (B)
        if 0 <= nx < COLS and 0 <= ny < FILAS:
            return mapa[ny][nx] in [V, B]
        return False

    def mover(self, mapa, jugadores):
        if time.time() > self.timer_mov:
            dirs = [(0,1), (0,-1), (1,0), (-1,0)]
            dx, dy = random.choice(dirs) # Movimiento más directo
            nx, ny = self.x + dx, self.y + dy
            if self.puede_moverse(nx, ny, mapa):
                self.x, self.y = nx, ny
            self.timer_mov = time.time() + self.velocidad

class EnemigoCazador(Enemigo):
    """(SLIME) Persigue jugadores"""
    def __init__(self, x, y):
        super().__init__(x, y, "SLIME")
        self.velocidad = 0.6 # Muy rápido

    def mover(self, mapa, jugadores):
        if time.time() > self.timer_mov:
            target = None
            min_dist = 999
            
            # Buscar jugador más cercano
            for p in jugadores.values():
                if p.vivo:
                    dist = abs(p.x - self.x) + abs(p.y - self.y)
                    if dist < min_dist and dist < 8: # Visión de 8 bloques
                        min_dist = dist
                        target = p

            # Algoritmo de persecución simple
            moved = False
            if target:
                dx = 1 if target.x > self.x else -1 if target.x < self.x else 0
                dy = 1 if target.y > self.y else -1 if target.y < self.y else 0
                
                # Intentar acercarse
                posibles = []
                if dx != 0: posibles.append((dx, 0))
                if dy != 0: posibles.append((0, dy))
                if not posibles: posibles = [(0,1), (0,-1), (1,0), (-1,0)]

                for mx, my in posibles:
                    nx, ny = self.x + mx, self.y + my
                    if self.puede_moverse(nx, ny, mapa):
                        self.x, self.y = nx, ny
                        moved = True
                        break
            
            # Si no persigue o está bloqueado, moverse al azar
            if not moved:
                dirs = [(0,1), (0,-1), (1,0), (-1,0)]
                dx, dy = random.choice(dirs)
                nx, ny = self.x + dx, self.y + dy
                if self.puede_moverse(nx, ny, mapa): self.x, self.y = nx, ny

            self.timer_mov = time.time() + self.velocidad