import random
import time
from config import *
# Importamos las nuevas clases
from game.entities import Jugador, Bomba, Explosion, EnemigoErratico, EnemigoFantasma, EnemigoCazador

class GameState:
    def __init__(self):
        self.mapa = [[V for _ in range(COLS)] for _ in range(FILAS)]
        self.jugadores = {} 
        self.bombas = []
        self.explosiones = []
        self.enemigos = []
        self.generar_nivel()

    def generar_nivel(self):
        # 1. Mapa Procedural
        for y in range(FILAS):
            for x in range(COLS):
                if x == 0 or x == COLS-1 or y == 0 or y == FILAS-1:
                    self.mapa[y][x] = R
                elif x % 2 == 0 and y % 2 == 0:
                    self.mapa[y][x] = R
                elif random.random() < 0.35: # Un poco más de basura para cubrir al fantasma
                    self.mapa[y][x] = B

        # 2. Zonas seguras
        safe_zones = [(1,1), (1,2), (2,1), (COLS-2, FILAS-2)]
        for (sx, sy) in safe_zones:
            self.mapa[sy][sx] = V

        # 3. Spawning Variado de Enemigos
        # Generamos 2 de cada tipo
        for _ in range(3): self.spawn_enemigo(EnemigoErratico) # Smiles
        for _ in range(2): self.spawn_enemigo(EnemigoFantasma) # Ghosts
        for _ in range(2): self.spawn_enemigo(EnemigoCazador)  # Slimes

    def spawn_enemigo(self, ClaseEnemigo):
        """Busca un lugar vacío aleatorio y pone un enemigo"""
        intentos = 0
        while intentos < 50:
            ex, ey = random.randint(3, COLS-3), random.randint(3, FILAS-3)
            if self.mapa[ey][ex] == V:
                self.enemigos.append(ClaseEnemigo(ex, ey))
                break
            intentos += 1

    def update(self):
        now = time.time()

        # A. Bombas
        for b in self.bombas[:]:
            if now >= b.tiempo_detonacion:
                self.detonar(b)
                self.bombas.remove(b)
                if b.owner_id in self.jugadores:
                    self.jugadores[b.owner_id].bombas_disponibles += 1

        # B. Explosiones
        for e in self.explosiones[:]:
            if now >= e.tiempo_fin:
                self.explosiones.remove(e)

        # C. Enemigos (Polimorfismo: Cada uno se mueve a su manera)
        for e in self.enemigos:
            if e.vivo:
                # Ahora pasamos 'jugadores' para que el Cazador pueda verlos
                e.mover(self.mapa, self.jugadores)
                
                # Checar colisión con Jugadores
                for p in self.jugadores.values():
                    if p.vivo and p.x == e.x and p.y == e.y:
                        p.vivo = False # Game Over para ese jugador

    def detonar(self, bomba):
        hit_cells = [(bomba.x, bomba.y)]
        dirs = [(0,1), (0,-1), (1,0), (-1,0)]

        for dx, dy in dirs:
            for i in range(1, bomba.radio + 1):
                nx, ny = bomba.x + dx*i, bomba.y + dy*i
                if not (0 <= nx < COLS and 0 <= ny < FILAS): break
                
                cell = self.mapa[ny][nx]
                if cell == R: break
                if cell == B:
                    self.mapa[ny][nx] = V
                    hit_cells.append((nx, ny))
                    break 
                hit_cells.append((nx, ny))
        
        self.explosiones.append(Explosion(hit_cells))
        
        for (hx, hy) in hit_cells:
            for e in self.enemigos:
                if e.x == hx and e.y == hy: e.vivo = False
            for pid, p in self.jugadores.items():
                if p.x == hx and p.y == hy: p.vivo = False

    def mover_jugador(self, pid, dx, dy):
        if pid not in self.jugadores: return
        p = self.jugadores[pid]
        if not p.vivo: return

        nx, ny = p.x + dx, p.y + dy
        if 0 <= nx < COLS and 0 <= ny < FILAS:
            if self.mapa[ny][nx] == V:
                if not any(b.x == nx and b.y == ny for b in self.bombas):
                    p.x, p.y = nx, ny

    def poner_bomba(self, pid):
        if pid not in self.jugadores: return
        p = self.jugadores[pid]
        if p.vivo and p.bombas_disponibles > 0:
            self.bombas.append(Bomba(p.x, p.y, pid))
            p.bombas_disponibles -= 1