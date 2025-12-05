import random
import time
from config import *
from game.entities import Jugador, Enemigo, Bomba, Explosion

class GameState:
    def __init__(self):
        self.mapa = [[V for _ in range(COLS)] for _ in range(FILAS)]
        self.jugadores = {} 
        self.bombas = []
        self.explosiones = []
        self.enemigos = []
        self.generar_nivel()

    def generar_nivel(self):
        # 1. Mapa Procedural (Algoritmo Bomberman clásico)
        for y in range(FILAS):
            for x in range(COLS):
                if x == 0 or x == COLS-1 or y == 0 or y == FILAS-1:
                    self.mapa[y][x] = R
                elif x % 2 == 0 and y % 2 == 0:
                    self.mapa[y][x] = R
                elif random.random() < 0.3:
                    self.mapa[y][x] = B # Basura

        # 2. Zonas seguras (Esquinas)
        safe_zones = [(1,1), (1,2), (2,1), (COLS-2, FILAS-2)]
        for (sx, sy) in safe_zones:
            self.mapa[sy][sx] = V

        # 3. Spawning Enemigos
        tipos = ["SMILE", "SMOKE", "SLIME"]
        for _ in range(6):
            ex, ey = random.randint(3, COLS-3), random.randint(3, FILAS-3)
            if self.mapa[ey][ex] == V:
                self.enemigos.append(Enemigo(ex, ey, random.choice(tipos)))

    def update(self):
        """Actualiza el mundo (Solo el HOST llama a esto)"""
        now = time.time()

        # A. Bombas
        for b in self.bombas[:]:
            if now >= b.tiempo_detonacion:
                self.detonar(b)
                self.bombas.remove(b)
                # Devolver bomba al jugador
                if b.owner_id in self.jugadores:
                    self.jugadores[b.owner_id].bombas_disponibles += 1

        # B. Explosiones
        for e in self.explosiones[:]:
            if now >= e.tiempo_fin:
                self.explosiones.remove(e)

        # C. Enemigos (IA Errática)
        for e in self.enemigos:
            if e.vivo and now > e.timer_mov:
                dirs = [(0,1), (0,-1), (1,0), (-1,0)]
                dx, dy = random.choice(dirs)
                nx, ny = e.x + dx, e.y + dy
                # Solo caminan en vacío
                if self.mapa[ny][nx] == V:
                    e.x, e.y = nx, ny
                e.timer_mov = now + (0.5 if e.tipo == "SMOKE" else 0.8)

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
                    self.mapa[ny][nx] = V # Destruir basura
                    hit_cells.append((nx, ny))
                    break # La explosión se detiene en la basura
                hit_cells.append((nx, ny))
        
        self.explosiones.append(Explosion(hit_cells))
        
        # Verificar Daño
        for (hx, hy) in hit_cells:
            # Matar Enemigos
            for e in self.enemigos:
                if e.x == hx and e.y == hy: e.vivo = False
            # Matar Jugadores
            for pid, p in self.jugadores.items():
                if p.x == hx and p.y == hy: p.vivo = False

    def mover_jugador(self, pid, dx, dy):
        if pid not in self.jugadores: return
        p = self.jugadores[pid]
        if not p.vivo: return

        nx, ny = p.x + dx, p.y + dy
        if 0 <= nx < COLS and 0 <= ny < FILAS:
            # Solo camina si está vacío y no hay bomba
            if self.mapa[ny][nx] == V:
                if not any(b.x == nx and b.y == ny for b in self.bombas):
                    p.x, p.y = nx, ny

    def poner_bomba(self, pid):
        if pid not in self.jugadores: return
        p = self.jugadores[pid]
        if p.vivo and p.bombas_disponibles > 0:
            self.bombas.append(Bomba(p.x, p.y, pid))
            p.bombas_disponibles -= 1